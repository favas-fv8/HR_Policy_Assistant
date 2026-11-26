from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db import transaction

from .serializers import ConversationSerializer, MessageSerializer
from .models import Conversation, Message
from .utils import generate_chat_title, is_default_chat_title


class ChatViewSet(viewsets.ViewSet):
    """Chat conversation management endpoints."""
    
    def list_conversations(self, request):
        """List all conversations for the current employee (exclude empty)."""
        conversations = (
            request.user.conversations
            .annotate(_msg_count=Count("messages"))
            .filter(_msg_count__gt=0)
            .order_by("-updated_at")
        )
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    def create_conversation(self, request):
        """Create a new conversation."""
        title = (request.data.get("title") or "New Chat").strip() or "New Chat"
        conversation = Conversation.objects.create(
            title=title,
            employee=request.user
        )
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(methods=["get"], detail=True)
    def messages(self, request, pk=None):
        """Get messages for a conversation."""
        conversation = get_object_or_404(Conversation, pk=pk)
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def delete_conversation(self, request, pk=None):
        """Delete a conversation."""
        conversation = get_object_or_404(Conversation, pk=pk)
        if conversation.employee != request.user and not request.user.is_hr_admin:
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=False, url_path="start")
    def start_conversation(self, request):
        """Create a conversation with the first message (no empty conversations persisted)."""
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response(
                {"error": "Message content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        title = generate_chat_title(content) or "New Chat"
        try:
            with transaction.atomic():
                conversation = Conversation.objects.create(
                    title=title,
                    employee=request.user,
                )
                Message.objects.create(
                    conversation=conversation,
                    role="user",
                    content=content,
                )
        except Exception:
            return Response(
                {"error": "Failed to create conversation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            from rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            rag_result = pipeline.answer_question(content)
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=rag_result.get("answer") or "",
                sources=rag_result.get("sources") or [],
            )
        except Exception:
            try:
                assistant_message = Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content="I'm sorry, but I encountered an error while processing your question. Please try again or contact support.",
                    sources=[],
                )
            except Exception:
                return Response(
                    {"error": "Failed to create assistant response."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        conv_data = ConversationSerializer(conversation).data
        payload = MessageSerializer(assistant_message).data
        payload["conversation_id"] = conversation.id
        payload["conversation"] = conv_data
        payload["conversation_title"] = conversation.title
        return Response(payload, status=status.HTTP_201_CREATED)
    
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
        
        try:
            from rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            rag_result = pipeline.answer_question(content)
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=rag_result.get("answer") or "",
                sources=rag_result.get("sources") or [],
            )
        except Exception:
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content="I'll help you find the answer to your HR policy question. Please wait while I retrieve relevant information from the policy documents.",
                sources=[],
            )
        
        payload = MessageSerializer(assistant_message).data
        payload["conversation_title"] = conversation.title
        return Response(payload)