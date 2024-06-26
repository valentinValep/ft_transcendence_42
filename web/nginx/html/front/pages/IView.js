/**
 * Represents a view in the application.
 * @interface
 */
export class IView {
	/**
	 * Checks if the view matches the current route.
	 * @param {string} route The route to match.
	 * @returns {boolean} True if the view matches the route, false otherwise.
	 */
	static match_route(route) {
		return false;
	}

	/**
	 * Renders the view.
	 */
	async render() {
		let main = document.querySelector("main");
		if (main === null)
			return;
		main.innerHTML = "<h1>Not implemented</h1>";
	}

	/**
	 * Make the view disappear and stop any ongoing processes.
	 */
	destroy() {
	}

	stop() {
	}
}