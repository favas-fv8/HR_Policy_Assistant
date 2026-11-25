from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import ConversationSerializer, MessageSerializer
from .models import Conversation, Message
from .utils import generate_chat_title, is_default_chat_title


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
        title = (request.data.get("title") or "New Chat").strip() or "New Chat"
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
        # Filter by employee access: employees can only access their own conversations
        # HR Admin can access all conversations
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied. You can only access your own conversations."},
                status=status.HTTP_403_FORBIDDEN
            )
        messages = conversation.messages.all()
        from .serializers import MessageSerializer
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def delete_conversation(self, request, pk=None):
        """Delete a conversation owned by the current user (or any for HR admin)."""
        conversation = get_object_or_404(Conversation, pk=pk)
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied. You can only delete your own conversations."},
                status=status.HTTP_403_FORBIDDEN
            )
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=True)
    def send_message(self, request, pk=None):
        """Send a message in a conversation."""
        conversation = get_object_or_404(Conversation, pk=pk)
        # Filter by employee access: employees can only access their own conversations
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied. You can only send messages to your own conversations."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"error": "Message content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if is_default_chat_title(conversation.title) and not conversation.messages.filter(role="user").exists():
            conversation.title = generate_chat_title(content)
            conversation.save(update_fields=["title", "updated_at"])

        message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=content
        )
        
        # Generate AI response using RAG pipeline
        try:
            from rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            rag_result = pipeline.answer_question(content)
            
            # Create assistant message with the generated answer and sources
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=rag_result["answer"],
                sources=rag_result["sources"]
            )
            
        except Exception as e:
            # If RAG pipeline fails, create a fallback assistant message
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=f"I'm sorry, but I encountered an error while processing your question. Please try again or contact support.",
                sources=[]
            )
        
        from .serializers import MessageSerializer
        msg_serializer = MessageSerializer(message)
        payload = MessageSerializer(assistant_message).data
        payload["conversation_title"] = conversation.title
        return Response(payload)