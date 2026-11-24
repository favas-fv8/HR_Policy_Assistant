from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ConversationSerializer, MessageSerializer
from .models import Conversation, Message


class ChatViewSet(viewsets.ViewSet):
    """Chat conversation management endpoints."""
    
    def list_conversations(self, request):
        """List all conversations for the current employee."""
        conversations = request.user.conversations.all()
        from .serializers import ConversationSerializer
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    def create_conversation(self, request):
        """Create a new conversation."""
        title = request.data.get("title", "New Conversation")
        conversation = Conversation.objects.create(
            title=title,
            employee=request.user
        )
        from .serializers import ConversationSerializer
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(methods=["get"], detail=True)
    def messages(self, request, pk=None):
        """Get messages for a conversation."""
        conversation = get_object_or_404(Conversation, pk=pk)
        # Filter by employee access
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        messages = conversation.messages.all()
        from .serializers import MessageSerializer
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(methods=["post"], detail=True)
    def send_message(self, request, pk=None):
        """Send a message in a conversation."""
        conversation = get_object_or_404(Conversation, pk=pk)
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"error": "Message content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=content
        )
        
        # TODO: Generate AI response using RAG pipeline
        # For now, create a placeholder assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="I'll help you find the answer to your HR policy question. Please wait while I retrieve relevant information from the policy documents.",
            sources={}
        )
        
        from .serializers import MessageSerializer
        msg_serializer = MessageSerializer(message)
        return Response(MessageSerializer(assistant_message).data)