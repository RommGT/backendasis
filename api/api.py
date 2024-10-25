# api.py

import os
import numpy as np
import cv2
from deepface import DeepFace
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import pandas as pd  # You can remove this import if not needed elsewhere
from datetime import datetime  # You can remove this import if not needed elsewhere
from .serializers import ApiSerializer, AttendanceRecordSerializer
from .models import Api, AttendanceRecord  # Import the new model

# Helper functions (keep decode_image)
def decode_image(image_file):
    # Read the image from the uploaded file
    image_data = image_file.read()
    image_np = np.frombuffer(image_data, dtype=np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    return image

class ApiViewSet(viewsets.ModelViewSet):
    queryset = Api.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = ApiSerializer
  # Método register
    @action(detail=False, methods=['post'])
    def register(self, request):
        if 'email' not in request.POST:
            return Response({"error": "Falta email"}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'images' not in request.FILES:
            return Response({"error": "Falta imagen"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_email = request.POST['email']
        images = request.FILES.getlist('images')
        
        if not user_email or not images:
            return Response({"error": "No hay imagen ni email"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear carpeta para el correo electrónico si no existe
        user_folder_path = os.path.join(settings.IMAGENES_DIR, user_email)
        if not os.path.exists(user_folder_path):
            os.makedirs(user_folder_path)
    
        # Guardar cada imagen en formato JPG en la carpeta correspondiente
        for index, image_file in enumerate(images):
            # Leer la imagen desde el archivo subido
            image_data = image_file.read()
            image_np = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
            # Generar el nombre del archivo basado en un índice
            image_filename = f'foto{index + 1}.jpg'
            image_path = os.path.join(user_folder_path, image_filename)
    
            # Guardar la imagen en formato JPG
            cv2.imwrite(image_path, image)
    
        return Response({"result": "ok"}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'])
    def authenticate(self, request):
        # Extract data from request and implement logic
        if 'image' not in request.FILES:
            return Response({"error": "No image file provided"},status=status.HTTP_200_OK)

        if 'email' not in request.data:
            return Response({"error": "No email provided"}, status=status.HTTP_200_OK)

        if 'class' not in request.data:
            return Response({"error": "No class provided"}, status=status.HTTP_200_OK)

        image_file = request.FILES['image']
        user_email = request.data['email']
        class_name = request.data['class']
        
        if not image_file or not user_email or not class_name:
            return Response({"error": "No image file, email, or class provided"}, status=status.HTTP_200_OK)

        # Decode the image from the file
        img = decode_image(image_file)

        # Temporarily save the uploaded image for comparison
        temp_image_path = os.path.join(settings.MEDIA_ROOT, f'{user_email}_temp.png')
        cv2.imwrite(temp_image_path, img)

        # Initialize the result as unknown
        best_match_email = "No se reconoce al usuario"
        best_match_score = float('inf')  # Lower score indicates better match

        # User's image directory
        user_folder_path = os.path.join(settings.IMAGENES_DIR, user_email)

        # Check if the user's folder exists
        if os.path.isdir(user_folder_path):
            for image_file_name in os.listdir(user_folder_path):
                image_path = os.path.join(user_folder_path, image_file_name)

                try:
                    # Anti-spoofing test in face detection
                    face_objs = DeepFace.extract_faces(
                         img_path=temp_image_path,
                         anti_spoofing = True
                    )
                    # Verify if all faces are real
                    all_faces_real = all(face_obj.get("facial_area") for face_obj in face_objs)

                    if not all_faces_real:
                        return Response({"error": "La cara no es real"}, status=status.HTTP_200_OK)

                    # Compare the uploaded image with the image in the user's folder
                    result = DeepFace.verify(temp_image_path, image_path, enforce_detection=False, model_name='Facenet')
                    
                    # Assuming the result has a 'distance' key for the score
                    score = result['distance']
                    
                    # Update the best result if it's better
                    if score < best_match_score:
                        best_match_score = score
                        best_match_email = user_email

                except Exception as e:
                    print(f"No se identificó el usuario: {e}")
        else:
            return Response({"error": "El usuario no existe"}, status=status.HTTP_200_OK)

        # Clean up temporary file
        if os.path.exists(temp_image_path):
            print(temp_image_path)
           # os.remove(temp_image_path)

        if best_match_score < 0.55:
            # Save attendance record to the database
            AttendanceRecord.objects.create(
                email=best_match_email,
                class_name=class_name
                # timestamp will be set automatically
            )
            return Response({"email": best_match_email})
        else:
            return Response({"error": "No se reconoce al usuario"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def historial(self, request):
        # Retrieve attendance records from the database
        attendance_records = AttendanceRecord.objects.all()
        serializer = AttendanceRecordSerializer(attendance_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
