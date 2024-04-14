import { IView } from "/front/pages/IView.js";
import { route } from "/front/pages/spa_router.js";
import { createRoomForm, joinRoomForm } from "../room/roomUtils.js";
import { NotifView, createNotificationSocket } from "../notif/NotifView.js";
import * as Login from "/front/pages/login/login.js";

export class LoggedHeaderView extends IView {
	async render() {
		let header_promise = fetch("/front/pages/home/header.html")
			.then(response => response.text())
			.then(html => document.querySelector("header").innerHTML = html);

		let user = await fetch("/api/user_management/me", {
			headers: { 'Authorization': `Token ${Login.getCookie('token')}` }
		}).then(response => response.json())
		await header_promise;

		this.notifSocket = createNotificationSocket(user.username);
		new NotifView().render();
	}

	destroy() {
		if (this.notifSocket)
			this.notifSocket.close();
	}
}

export class HomeView extends IView {
	static match_route(route) {
		return route === "/home";
	}

	async render() {
		await fetch("/front/pages/home/home.html")
			.then(response => response.text())
			.then(html => document.querySelector("main").innerHTML = html);

		document.querySelector(".centered_box").addEventListener("click", (e) => {
			switch (e.target.id)
			{
				case "game":
					route("/game");
					break;
				case "join":
					document.querySelector('.joinRoomForm').classList.toggle('show');
					document.getElementById("inputRoomCode").focus();
					if (document.querySelector('.createRoomSelect').classList.contains('show'))
						{ document.querySelector('.createRoomSelect').classList.remove('show'); }
					break;
				case "create":
					document.querySelector('.createRoomSelect').classList.toggle('show');
					if (document.querySelector('.joinRoomForm').classList.contains('show'))
						{ document.querySelector('.joinRoomForm').classList.remove('show'); }
					break;
				case "me":
					route("/me");
					break;
			}
		});
		createRoomForm(); // from room.js
		joinRoomForm(); // from room.js
	}

	destroy() {
	}
}

export async function footer()
{
	return await fetch("/front/pages/home/footer.html").then(response => response.text());
}