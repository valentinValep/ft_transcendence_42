/**
 * Min players in tournament : 8
 * Max players in tournament : 36
 *
 * Only first round should accept less than 6 players
 *
 * Minimum 1 player shouild be eliminated in each game
 *
 *
 */

import * as Login from "/front/pages/login/login.js";
import { IView } from "/front/pages/IView.js";
import { route } from "/front/pages/spa_router.js";
import { checkRoomCode } from "/front/pages/room/roomUtils.js";
import { getRoomInfo, getTournmentInfo, getRoundInfo, fillRoundMap, displayMyPool, renamePools, displayAPool} from "/front/pages/room/tournamentUtils.js";
import { createTournament } from "./tournamentUtils.js";

export class TournamentView extends IView {
	static match_route(route) {
		if (route.split("/")[1] === "tournament" && route.split("/")[2].length === 6 && route.split("/")[2] !== undefined) {
			return true;
		} else {
			return false;
		}
	}

	async render() {
		let code = document.URL.split("/")[4];
		let roomExists = await checkRoomCode(code);
		if (roomExists === false) {
			route("/unknown");
			return;
		}

		let roomInfo = await getRoomInfo(code)
		let tournament = await getTournmentInfo(roomInfo.room_id)
		let roundInfo = await getRoundInfo(tournament.id, tournament.current_round)

		let html = await fetch("/front/pages/room/tournament.html").then(response => response.text());
		document.querySelector("main").innerHTML = html;

		let pools = renamePools(roundInfo.distribution);

		fillRoundMap(tournament, pools);
		displayMyPool(pools);
		displayAPool(pools);

		this.TournamentSocket = createTournamentSocket(tournament.id);
	}

	destroy() {
		console.log("Destroying tournament view");
		if (this.TournamentSocket) {
			this.TournamentSocket.close();
		}
	}
}

export function createTournamentSocket(tournament_id) {
	console.log("Creating tournament socket for tournament: ", tournament_id);
	const TournamentSocket = new WebSocket(
		'ws://'
		+ window.location.host
		+ '/ws/tournament/'
		+ tournament_id,
	);
	console.log(TournamentSocket);

	TournamentSocket.onerror = function (e) {
		console.log('Tournament - Socket error', e);
		// route('/home');
	};

	TournamentSocket.onopen = function (e) {
		console.log('Tournament - Socket successfully connected: ', e);

	};

	TournamentSocket.onclose = function (e) {
		console.log('Tournament - Socket closing:', e.code, e.reason);
		const code = e.code;
		const reason = e.reason;
		switch (code) {
			case 1000:
				console.log('Tournament - Socket closed normally.');
				break;
			case 3010:
				console.log('Tournament - Player not invited to tournament');
				route('/playerNotInvited');
				break;
			case 3011:
				console.log('Tournament - Player was eliminated');
				route('/playerEliminated');
				break;
			default:
				console.log('Tournament - Socket closed unexpectedly:', code, reason);
		}
	};

	TournamentSocket.onmessage = function (e) {
		const data = JSON.parse(e.data);
		const type = data.type;
		switch (type) {
			case "player_eliminated":
				console.log("Player eliminated:", data);
				playerEliminated(data);
				break;
			// case "round_start":
			// 	console.log("Round starting:", data);
			// 	break;
			// case "round_end":
			// 	console.log("Round ending:", data);
			// 	break;
			// case "tournament_end":
			// 	console.log("Tournament ending:", data);
			// 	break;
			default:
				console.error("Unknown message type:", data.type);
				break;
		}
	};

	return TournamentSocket;

}