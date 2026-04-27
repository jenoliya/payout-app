from django.shortcuts import render
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status

# serializers
from .serializers import CreateMerchantSerializer

# Create your views here.
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
# class StudentView(APIView):
#     serializer_class = StudentSerializer
#     def get(self, request):
#         # select records from students model
#         students = Student.objects.all()
#         # serialize students
#         serializer = self.serializer_class(students, many=True)
#         output = {
#             "message" : "Student list",
#             "student_list": serializer.data
#         }
#         first_task.delay()
#         return Response(output, status=status.HTTP_200_OK)
#     def post(self, request):
#         # print(request.data)
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         output={
#             "message": "New student record created",
#             "student": serializer.data
#         }
#         return Response(output, status=status.HTTP_201_CREATED)