import { GameContext } from "/front/pages/game/scripts/pong.js";
import { IView } from "/front/pages/IView.js";

export class GameView extends IView {
	static match_route(route) {
		const regex = new RegExp("^/game/[0-9]+$");
		console.log("GameView.match_route", route, regex.test(route));
		return regex.test(route);
	}

	async render() {
		let ready_state = 0;
		let main = document.querySelector("main");
		let main_set = false;

		//let particule = document.getElementsByClassName("particles-js-canvas-el");
		//if (particule.length > 0)
		//	particule[0].remove();

		let footer = document.querySelector("footer");
		if (footer !== null)
			footer.remove();

		await fetch("/front/pages/game/game.html").then(response => response.text()).then(html => {
			main.innerHTML = html;
			main_set = true;

		});

		let stylesheet = document.createElement("link");
		stylesheet.rel = "stylesheet";
		stylesheet.href = "/front/pages/game/style.css";
		stylesheet.onload = () => {
			ready_state++;
		};
		document.head.appendChild(stylesheet);

		//let script = document.createElement("script");
		//script.src = "/front/pages/game/scripts/pong.js";
		//script.type = "module";
		//script.onload = () => {
		//	ready_state++;
		//};

		while (!main_set)
			await new Promise(resolve => setTimeout(resolve, 100));
		//main.appendChild(script);

		while (ready_state < 1)
			await new Promise(resolve => setTimeout(resolve, 100));

		try {
			const game_id = document.URL.split("/")[4];
			let game = new GameContext(game_id);

			await game.load();
			game.run();
		}
		catch (e) {
			console.error("Game error", e);
		}
	}

	destroy() {
	}
}
