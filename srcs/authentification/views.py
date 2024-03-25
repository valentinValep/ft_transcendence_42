from django.http import HttpResponse
from user_management.models import Player
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer

@api_view(['POST'])
def login(request):
	try:
		user = Player.objects.get(username=request.data['username'])
		if not user.check_password(request.data['password']):
			return Response({"error" : "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)
		token, created = Token.objects.get_or_create(user=user)
		serializer = UserSerializer(instance=user)
		return Response({ "token" : token.key, "user" : serializer.data }, status=status.HTTP_200_OK)
	except Player.DoesNotExist:
		return Response({ "error" : "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def signup(request):
	serializer = UserSerializer(data=request.data)
	if not (serializer.is_valid()):
		return Response({"error" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
	users = serializer.save()
	if users:
		token = Token.objects.create(user=users)
		# you can update the token by: token.key = token.generate_key() and then calling save()
		json = serializer.data
		json['token'] = token.key
		return Response(serializer.data, status= status.HTTP_201_CREATED)



@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def check_token(request):
	print("Request auth")
	return Response({"message" : "OK"})
