import random
import os
import re
from django.http import HttpResponse
from user_management.models import Player
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import PlayerSerializer
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.response import Response
from rest_framework import status
import requests
import qrcode
import io

##### Authentication #####

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def login(request):
	try:
		print(request.data)
		user = Player.objects.get(username=request.data['username'])
		if not user.check_password(request.data['password']):
			return Response({"error" : "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)
		token, _ = Token.objects.get_or_create(user=user)
		print("Token : ", token.key)
		serializer = PlayerSerializer(instance=user)
		return Response({ "token" : token.key, "user" : serializer.data }, status=status.HTTP_200_OK)
	except Player.DoesNotExist:
		return Response({ "error" : "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def check_token(request):
	"""
	Communication endpoint to check if a token is valid for other services
	"""
	dico = {
		"id" : request.user.id,
		"user" : request.user.username,
	}
	if request.user.twoFA == True and request.user.valid_twoFA == False:
		return Response({"error" : "2FA not valid"}, status=status.HTTP_400_BAD_REQUEST)
	return Response({"message": "Token is valid", "user" : dico}, status=status.HTTP_200_OK)

##### Registration #####

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def signup(request):
	serializer = PlayerSerializer(data=request.data)
	if not serializer.is_valid():
		print("error : ", serializer.errors)
		if 'email' in serializer.errors:
			return Response({"error" : "Email already used"}, status=status.HTTP_400_BAD_REQUEST)
		if 'username' in serializer.errors:
			return Response({"error" : "Username already used or invalid"}, status=status.HTTP_400_BAD_REQUEST)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	# regex = lowercase, uppercase, numbers, hyphens, underscores, between 3 and 10 characters
	username_pattern = r'^[a-zA-Z0-9_-]+$'
	if not re.match(username_pattern, request.data["username"]):
		return Response({"error": "Username must contain only letters, numbers, hyphens, and underscores"}, status=status.HTTP_400_BAD_REQUEST)
	elif len(request.data["username"]) < 3 or len(request.data["username"]) > 15:
		return Response({"error": "Username must be between 3 and 10 characters"}, status=status.HTTP_400_BAD_REQUEST)
	if not request.data.get("third_party", False):
		password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])'
		if not re.match(password_pattern, request.data["password"]):
			return Response({"error": "Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number and 1 special character"}, status=status.HTTP_400_BAD_REQUEST)
		elif len(request.data["password"]) < 6:
			return Response({"error": "Passsword must be at least 6 characters"}, status=status.HTTP_400_BAD_REQUEST)

	serializer.save()
	user = Player.objects.get(username=request.data["username"])
	# random avatar file from /front/ressources/img/png/avatar_XXX.png
	avatar_file = "/front/ressources/uploads/avatar_0" + str(random.randint(0, 8)) + ".png"
	user.avatar_file = avatar_file
	user.save()
	token = Token.objects.create(user=user)
	return Response({"token" : token.key, "user" : serializer.data}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def forty2_auth(request):
	print(request.data)
	data = {
		'grant_type': 'authorization_code',
		'client_id': 'u-s4t2ud-778802c450d2090b49c6c92d251ff3d1fbb51b03a9284f8f43f5df0af1dae8fa',
		'client_secret': os.environ.get('SECRET_KEY_42'),
		'code': request.data['code'],
        'redirect_uri': 'https://localhost:8080/forty2',
	}
	print(data)
	response = requests.post("https://api.intra.42.fr/oauth/token", data=data)
	data = response.json()
	if 'error' in data.keys():
		return Response(data, status=status.HTTP_400_BAD_REQUEST)
	print(data)
	return Response(data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_42_mail(request):
	bearer = request.META.get('HTTP_AUTHORIZATION')
	response = requests.get("https://api.intra.42.fr/v2/me", headers = {'Authorization': bearer})
	if response.status_code != 200:
		return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)
	return Response(response.json(), status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def google_auth(request):
	print(request.data)
	data = {
		'grant_type': 'authorization_code',
		'client_id': '646881961013-bgo5lf3ru7bc1869b12ushtq3q2irgah.apps.googleusercontent.com',
		'client_secret': os.environ.get('SECRET_KEY_GOOGLE'),
		'code': request.data['code'],
        'redirect_uri': 'https://localhost:8080/google',
	}
	print(data)
	response = requests.post("https://oauth2.googleapis.com/token", data=data)
	data = response.json()
	if 'error' in data.keys():
		return Response(data, status=status.HTTP_400_BAD_REQUEST)
	print("Google", data)
	return Response(data)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def is_registered(request):
	try:
		user = Player.objects.get(email=request.data['email'])
		token, created = Token.objects.get_or_create(user=user)
		serializer = PlayerSerializer(instance=user)
		return Response({ "token" : token.key, "user" : serializer.data }, status=status.HTTP_200_OK)
	except Player.DoesNotExist as error:
		print("In is_register", error)
		return Response({"error" : "User not registered"}, status=status.HTTP_401_UNAUTHORIZED)

def get_user_totp_device(user, confirmed=None):
	devices = devices_for_user(user, confirmed=confirmed)
	for device in devices:
		if isinstance(device, TOTPDevice):
			return device

@api_view(['GET'])
def TOTPCreateView(request):
	user = request.user
	device = get_user_totp_device(user)
	if not device:
		device = user.totpdevice_set.create(confirmed=False)
	url = device.config_url
	print("url:", url)
	qr = qrcode.QRCode(
		version=1,
		error_correction=qrcode.constants.ERROR_CORRECT_L,
		box_size=10,
		border=4,
	)
	qr.add_data(url)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	img_byte_array = io.BytesIO()
	img.save(img_byte_array, format='PNG')
	img_byte_array.seek(0)
	response = HttpResponse(img_byte_array.getvalue(), content_type='image/png', status=status.HTTP_201_CREATED)
	response['Content-Disposition'] = 'attachment; filename="qrcode.png"'
	print("Response: ", response)
	return response

@api_view(['POST'])
def TOTPVerifyView(request):
	"""
	Use this endpoint to verify/enable a TOTP device
	"""
	print("TOTPVERIFY TA RACE !!!!!!!!!!!!!!!")
	print(request.data)
	if not "token" in request.data:
		print("No token")
		return Response(status=status.HTTP_400_BAD_REQUEST)
	token = request.data["token"]
	user = request.user
	device = get_user_totp_device(user)
	print("device : ", device)
	if not device == None and device.verify_token(token):
		if not device.confirmed:
			device.confirmed = True
			device.save()
		request.user.valid_twoFA = True
		request.user.save()
		return Response(True, status=status.HTTP_200_OK)
	return Response(False, status=status.HTTP_400_BAD_REQUEST)
