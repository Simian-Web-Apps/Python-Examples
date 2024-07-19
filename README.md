# Simian Examples for Python

Simian GUI offers a low-code solution for creating web apps using Python, MATLAB, and Julia, expediting development and ensuring a smooth journey from concept to production. By leveraging accessible web technologies such as form.io, DataTables, and Plotly, it facilitates the creation of apps for complex tasks like calculations and data visualization.
 
With an intuitive two-pillar approach to app development, Simian GUI simplifies the process of building and adding interaction, offering options like an app builder or low-code programmatic approach. It also provides utilities to easily manage web events and backend functionalities, eliminating the need for tailored API definitions.
 
During runtime, the Simian frontend renders the defined web app directly from Python, MATLAB, or Julia code in the web browser, without requiring front-end developer involvement. This streamlined workflow allows users to craft and deploy apps locally with ease, making Simian GUI a comprehensive solution for web app development from inception to production.

## Getting Started

### Dependencies

* Simian GUI runs and is tested on Python `3.8` to `3.12`.

### Installing

* Simian GUI consists of four packages that can be installed via pip:

    * `simian-gui` contains the core functionality, with optional dependency on Redis

    * `simian-local` allows running locally using pywebview

    * `simian-examples` contains the the same examples available in the `simian/examples` folder in this repository

    * `simian-builder` contains the builder

    ```
    pip install --extra-index-url https://pypi.simiansuite.com/simple/ simian-gui[redis] simian-local simian-examples simian-builder
    ```

### Running Examples

#### Online

Example web apps are deployed at the [Simian Web Apps Demo portal](https://demo01.simiansuite.com/)

#### Local

For running apps locally, we assume that the `src` folder is on the Python path. The most straightforward way to achieve this, is to make it the current folder before running Python.

* **All components**: this example contains all components that can be used in Simian GUI.
    ```
    import simian.local
    simian.local.Uiformio("simian.examples.all_components", window_title="All Components")
    ```

* **Ball Thrower**: this example uses the `scipy.integrate.solve_ivp` solver to calculate the trajectory of a ball being thrown. Hence, the `scipy` package must be installed as a dependency.
    ```python
    from simian.local import Uiformio
    Uiformio("simian.examples.ballthrower", window_title="Ball Thrower")
    ```
    See [Example](https://doc.simiansuite.com/simian-gui/example.html) in the documentation for more details.

* **Plot types**: this example showcases the Plotly integration in Simian GUI.
    ```python
    from simian.local import Uiformio
    Uiformio("simian.examples.plottypes", window_title="Plot Types")
    ```

* **Hypotheek planner**: this example is an (indicative) mortgage planner. Available in Dutch only.
    ```python
    from simian.local import Uiformio
    Uiformio("hypoplanner.hypo_planner", window_title="Hypotheek Planner")
    ```

* **Bird swarm**: this example uses a particle swarm optimization to simulate bird feeding behavior.
    * Install additional dependencies
        ```
        pip install cython setuptools matplotlib scipy noise
        ```
    * Use Cython to build the `.pyx` modules
        ```
        cd birdswarm
        python setup.py build_ext --inplace
        ```
    * Run the application
        ```python
        from simian.local import Uiformio
        Uiformio("birdswarm.bird_swarm", window_title="Bird Swarm")
        ```

### Running Builder

* Start the Builder by running
    ```
    python -m simian.builder
    ```

* Fill in the fields in the *Options* section and click *Create module* to create the module.

* Add, remove and modify components and click *Save JSON* to save your changes.

* Click *Preview application* to run your Simian Web App.

* See [Simian Form Builder](https://doc.simiansuite.com/simian-gui/builder.html) for more information.

### Building an App

* A Simian Web App is a module containing two functions: `gui_init` to define the form and `gui_event` to handle events.
    ```python
    from simian.gui import Form, component, utils
    
    def gui_init(meta_data: dict) -> dict:
        # Create a form and set a logo and title.
        form = Form()

        payload = {
            "form": form,
            "navbar": {
                "logo": "favicon.ico",
                "title": "Hello, World!",
            },
        }

        return payload

    def gui_event(meta_data: dict, payload: dict) -> dict:
        # Process the events.
        return payload
    ```

* See the [Hello world](https://doc.simiansuite.com/simian-gui/setup/hello.html) example in the documentation for how to program a Simian Web App.

## Help

In case of issues or questions, please see the [issue tracker](https://github.com/Simian-Web-Apps/Issue-Tracker).

## Contributing

Any contributions to the examples are greatly appreciated.

If you have an example that you would like to share, please fork the repo and create a pull request. Don't forget to give the project a star! Thanks again!

1. Fork the Project

2. Create your Feature Branch (git checkout -b feature/AmazingExample)

3. Commit your Changes (git commit -m 'Add some Amazing Example')

4. Push to the Branch (git push origin feature/AmazingExample)

5. Open a Pull Request

## Authors

* [MonkeyProof Solutions](https://monkeyproofsolutions.nl)

## Version History

See the [Release notes](https://doc.simiansuite.com/simian-gui/release_notes.html) in the documentation for the version history.

## License

The Simian Examples are licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* [Form.io](https://form.io)
* [Plotly](https://plotly.com)
* [DataTables](https://datatables.net/)
* [Pywebview](https://pywebview.flowrl.com/)
