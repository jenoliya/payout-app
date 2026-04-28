from django.shortcuts import render
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status

# serializers
from .serializers import CreateMerchantSerializer

# create new merchant
class MerchantView(APIView):
    serializer_class = CreateMerchantSerializer
    def post(self, request):
        # print(request.data)
        
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create()
        output={
            "message": "New merchant record created",
            "merchant": serializer.data
        }
        return Response(output, status=status.HTTP_201_CREATED)