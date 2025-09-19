/**
 * Initialize function for the image slider. Called by the extension component.
 * @param {object} component Extension component data.
 */
async function initImageSlider(component) {
    component.internal.initReady = new Promise((resolve) => {
        window.customElements.whenDefined("img-comparison-slider").then(() => {
            let observer = new MutationObserver((mutations, observer) => {
                observer.disconnect();
            imgSlider = component.container.getElementsByTagName("img-comparison-slider")[0];

            imgSlider.addEventListener("slide", (e) => {
                value = { ...component.value };
                value.sliderValue = Math.round(1000 * e.target.exposure) / 1000;

                // Emit the value change for validation, calculateValue, etc.
                component.valueChange.emit(value);
            });

            component.internal.imgSlider = imgSlider;
            // component.internal.imgSliderInput = imgSliderInput;
            component.internal.beforeImg = imgSlider.querySelector(".before img");
            component.internal.afterImg = imgSlider.querySelector(".after img");
    
                resolve(true);
            });

            observer.observe(component.container, { attributes: true, childList: true, subtree: true });

            component.container.innerHTML = `
            <img-comparison-slider class="img-comparison-slider w-100">
                <figure slot="first" class="before">
                    <img class="w-100">
                    <figcaption>Before</figcaption>
                </figure>
                <figure slot="second" class="after">
                    <img class="w-100">
                    <figcaption>After</figcaption>
                </figure>
            </img-comparison-slider>
            `;
        });
    });
}

/**
 * Update function for the image slider. Called by the extension component.
 * @param {object} component Extension component data.
 */
async function updateImageSlider(component) {
    component.internal.initReady.then(() => {
        component.internal.imgSlider.direction = component.value.direction;
        component.internal.imgSlider.hover = false;
        component.internal.imgSlider.keyboard = true;
        component.internal.imgSlider.value = component.value.sliderValue;

        if (component.value.img1Url && component.value.img2Url) {
            component.internal.beforeImg.src = component.value.img1Url;
            component.internal.afterImg.src = component.value.img2Url;
        } else {
            component.internal.beforeImg.src = getDefaultImage(1);
            component.internal.afterImg.src = getDefaultImage(2);
        }
    });
}

/**
 * Hardcoded default values for the images.
 * @param {int} idx Image number (1: left, 2: right)
 * @returns Data URI.
 */
function getDefaultImage(idx) {
    if (idx == 1) {
        slotSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="16" fill="grey" class="bi bi-1-circle" viewBox="-16 0 48 16">
            <rect width="48" height="16" x="-16" y="0" fill="lightgrey" />
            <path d="M1 8a7 7 0 1 0 14 0A7 7 0 0 0 1 8m15 0A8 8 0 1 1 0 8a8 8 0 0 1 16 0M9.283 4.002V12H7.971V5.338h-.065L6.072 6.656V5.385l1.899-1.383z" />
        </svg>
        `;
    } else {
        slotSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="16" fill="lightgrey" class="bi bi-1-circle" viewBox="-16 0 48 16">
            <rect width="48" height="16" x="-16" y="0" fill="grey" />
            <path d="M1 8a7 7 0 1 0 14 0A7 7 0 0 0 1 8m15 0A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.646 6.24v.07H5.375v-.064c0-1.213.879-2.402 2.637-2.402 1.582 0 2.613.949 2.613 2.215 0 1.002-.6 1.667-1.287 2.43l-.096.107-1.974 2.22v.077h3.498V12H5.422v-.832l2.97-3.293c.434-.475.903-1.008.903-1.705 0-.744-.557-1.236-1.313-1.236-.843 0-1.336.615-1.336 1.306" />
        </svg>
        `;
    }

    slotUrl = 'data:image/svg+xml;base64,' + btoa(slotSvg);

    return slotUrl
}

/**
 * Enforce minimum and maximum value for the number input.
 * @param {float} el Number input element.
 */
function enforceMinMax(el) {
    if (el.value != "") {
        if (parseInt(el.value) < parseInt(el.min)) {
            el.value = el.min;
        }
        if (parseInt(el.value) > parseInt(el.max)) {
            el.value = el.max;
        }
    }
}
