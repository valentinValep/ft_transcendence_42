from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
import requests
from decouple import config

from rooms.models import Rooms, Tournament, Occupy, Round
from .view_utils import CheckPlayerAccess, getWinnerId, update_tournament

def tournament_serializer(tournament, occupancy):
	"""
	Serialize a tournament object

	Args:
	- tournament: Tournament object

	Returns:
	- tournament_data: Dictionary containing tournament data :
		room_id
		total_rounds
		current_round
	"""
	tournament_data = {
		"id": tournament.id,
		"total_rounds": tournament.total_rounds,
		"current_round": tournament.current_round,
		"occupancy": occupancy,
	}
	return tournament_data

@api_view(['POST'])
def create_tournament(request, roomId):
	"""
	Create a new tournament

	Args:
	- request: Request object
	- roomId: Room ID

	Returns:
	- tournament_data: Dictionary containing tournament data :
		room_id
		total_rounds
		current_round
	"""
	tournament_data = {
		"room_id": roomId,
		"room_code": "",
		"total_rounds": 0,
		"current_round": 0,
		"occupancy": 0,
		"repartition": []
	}

	try:
		room = Rooms.objects.get(room_id=roomId)
		room_CODE = room.code
		contestants = Occupy.objects.filter(room_id=roomId)
		occupancy = len(contestants)

		total_rounds = (occupancy + 6) // 7

		tournament = Tournament.objects.create(room_id=room, total_rounds=total_rounds)

		tournament_data['id'] = tournament.id
		tournament_data['room_id'] = roomId
		tournament_data['room_code'] = room_CODE
		tournament_data['total_rounds'] = total_rounds
		tournament_data['current_round'] = 0
		tournament_data['occupancy'] = occupancy

		return JsonResponse(tournament_data)
	except Rooms.DoesNotExist:
		return JsonResponse({"error": "Room does not exist"})

@api_view(['GET'])
def tournamentInfo(request, room_id):
	"""
	get tournament data

	Args:
	- request: Request object
	- code: Room code

	Returns:
		json response containing tournament data
	"""
	try:
		room = Rooms.objects.get(room_id=room_id)
		contestants = Occupy.objects.filter(room_id=room)
		occupancy = len(contestants)
		tournament = Tournament.objects.get(room_id=room)
		update_tournament(tournament.id)
		tournament = Tournament.objects.get(room_id=room)
		return JsonResponse(tournament_serializer(tournament, occupancy))
	except Exception as e:
		return JsonResponse({"error": str(e)})
	

@api_view(['GET'])
def roundInfo(request, tournament_id, round_number):
	"""
	Get round informations

	Args:
	- request: Request object
	- tournament_id: Tournament ID

	Returns:
	- res: Dictionary containing round data
		- round_id
		- round_number
		- tournament_id
		- distribution
		- start_time
	"""
	round_data = {
		"round_id": 0,
		"round_number": 0,
		"tournament_id": "",
		"start_time": 0
	}

	try:
		res = {}
		tournament = Tournament.objects.get(id=tournament_id)

		print(round_number)
		round = Round.objects.get(tournament_id=tournament, round_number=round_number)
		url = f"http://proxy/api/game/retrieve_round/{round.id}"
		headers = {
					'Authorization': f"App {config('APP_KEY')}"
		}
		response = requests.get(url, headers=headers)
		res['distribution'] = response.json()

		round_data['round_id'] = round.id
		round_data['round_number'] = round.round_number
		round_data['tournament_id'] = tournament_id
		round_data['start_time'] = round.date_start

		res['round_data'] = round_data

		return JsonResponse(res)
	except Exception as e:
		return JsonResponse({"error": str(e)})


@api_view(['GET'])
def round_start_time(request, tournament_id, round_number):
	try:
		tournament = Tournament.objects.get(id=tournament_id)
		round = Round.objects.get(tournament_id=tournament, round_number=round_number)
		return JsonResponse({"start_time": round.date_start})
	except Exception as e:
		return JsonResponse({"error": str(e)})

@api_view(['GET'])
def get_round_code(request, round_id):
	"""
	Return the room code of the game with the given round_id

	json response format:
	{
		room_code: "room_code"
	}
	"""
	try:
		round = Round.objects.get(id=round_id)
		code = round.tournament_id.room_id.code

		return JsonResponse({
			"room_code": code
		})
	except Exception as e:
		return JsonResponse({"error": str(e)})

@api_view(['GET'])
def tournament_access(request, tournament_id, user_id):
	"""
	Check if the user has access to the tournament

	Args:
	- request: Request object
	- tournament_id: Tournament ID

	Returns:
	- JsonResponse: Response object
	"""
	res = {
		'access': CheckPlayerAccess(user_id, tournament_id)
	}

	return JsonResponse(res)

@api_view(['GET'])
def check_tournament_status(request, tournament_id):
	try:
		tournament = Tournament.objects.get(id=tournament_id)
		if (tournament.current_round == tournament.total_rounds):
			round = Round.objects.get(tournament_id=tournament, round_number=tournament.current_round)
			url = f"http://proxy/api/game/retrieve_round/{round.id}"
			headers = {
					"Content-Type": "application/json",
					'Authorization': f"App {config('APP_KEY')}"
			}
			rounds = requests.get(url, headers=headers)

			for game in rounds.json().values():
				if game['end_status'] == None:
					return JsonResponse({"status": "ongoing"})
			winner = getWinnerId(tournament_id)
			return JsonResponse({
				"status": "finished",
				"winner": winner,
				})
		else:
			return JsonResponse({"status": "ongoing"})
	except Exception as e:
		return JsonResponse({"error": str(e)})
