from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from user_management.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    password =  serializers.CharField(write_only=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']

    def validation_email(self, value):
        if (value.count('@') != 1):
            raise serializers.ValidationError("Invalid email format")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = self.Meta.model(**validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user
