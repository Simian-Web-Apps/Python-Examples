/**
 * The attach method is called after "render" which takes the rendered contents
 * from the render method (which are by this point already added to the DOM), and
 * then "attach" this component logic to that HTML. This is where you would load
 * any references within your templates (which use the "ref" attribute) to assign
 * them to the "this.refs" component variable using the loadRefs method.
 * 
 * @param element The parent DOM tree element that contains the extension component.
 * @returns Promise that will resolve when the attach code is ready.
 */
async function attachImageSlider(element) {
    this.loadRefs(element, {
        extension: 'single',
    });

    // Get the Extension component's html <div> container with ref="extension".
    let container = this.refs.extension;

    if (container) {
        // This function is asynchronous, so here we wait for the custom img-comparison-slider tag to be defined.
        await window.customElements.whenDefined("img-comparison-slider");

        return new Promise((resolve) => {
            // Before we can assign event listeners, we need to wait for the elements to be created in the DOM tree.
            // Hence, we set up an observer to wait for the elements to be created.
            let observer = new MutationObserver((mutations, observer) => {
                observer.disconnect();

                let imgSlider = container.getElementsByTagName("img-comparison-slider")[0];

                imgSlider.addEventListener("slide", (e) => {
                    let value = this.getValue();
                    value.sliderValue = Math.round(1000 * e.target.exposure) / 1000;
                    this.setValue(value);
                });

                this.setValue(this.dataValue);
                resolve(true);
            });

            observer.observe(container, { attributes: true, childList: true, subtree: true });

            // Now we can change the elements in the component, using the custom img-comparison-slider tag.
            container.innerHTML = `
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
    }
};

/**
 * Returns the value of the "view" data for this component.
 *
 * @return The value for this whole component.
 */
function getValueImageSlider() {
    let container = this.refs.extension;
    let imgSlider = container.getElementsByTagName("img-comparison-slider")[0];

    return {
        "sliderValue": imgSlider.value,
        "direction": imgSlider.direction,
        "img1Url": imgSlider.querySelector(".before img").src,
        "img2Url": imgSlider.querySelector(".after img").src,
    }
}


/**
 * Sets the value of both the data and view of the component (such as setting the
 * <input> value to the correct value of the data. This is most commonly used
 * externally to set the value and also see that value show up in the view of the
 * component. If you wish to only set the data of the component, like when you are
 * responding to an HTML input event, then updateValue should be used instead since
 * it only sets the data value of the component and not the view. 
 *
 * @param value The value that is being set for this component's data and view.
 * @param flags Change propagation flags that are being used to control behavior of the
 *              change propagation logic.
 */
function setValueImageSlider(value, flags) {
    let container = this.refs.extension;

    if (container) {
        let imgSlider = container.getElementsByTagName("img-comparison-slider")[0];

        // Setting the direction triggers another value change. Hence, we check the value to avoid infinite recursion.
        if (imgSlider.direction !== value.direction) {
            imgSlider.direction = value.direction;
        }

        imgSlider.value = value.sliderValue;
        imgSlider.querySelector(".before img").src = value.img1Url ?? getDefaultImage(1);
        imgSlider.querySelector(".after img").src = value.img2Url ?? getDefaultImage(2);
    }
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
