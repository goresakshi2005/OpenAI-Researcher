import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from .models import Conversation, Message
from .serializers import MessageSerializer, ConversationSerializer
from . import services

def get_or_create_conversation(request):
    """Get or create a conversation for the current session."""
    # Allow explicit conversation lookup via request (frontend can pass `conversation_id`) to avoid relying on cookies.
    conversation_id = None
    if request.method == 'POST':
        conversation_id = request.data.get('conversation_id')
    else:
        conversation_id = request.GET.get('conversation_id')

    if conversation_id:
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            pass

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    conversation, created = Conversation.objects.get_or_create(session_key=session_key)
    return conversation

@api_view(['POST'])
def chat(request):
    """Handle chat message: user input -> assistant response."""
    user_input = request.data.get('message', '').strip()
    use_web_search = request.data.get('use_web_search', True)  # default True

    if not user_input:
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    conversation = get_or_create_conversation(request)

    # Retrieve the most recent 10 messages in chronological order (oldest first)
    recent_messages = conversation.messages.order_by('-timestamp')[:10]
    history_messages = list(reversed(recent_messages))  # now oldest first
    history_list = [{'role': m.role, 'content': m.content} for m in history_messages]

    # Determine previous user input, assistant response, and low-rating flag
    previous_user_input = None
    previous_response = None
    low_rating_flag = False

    # Get the most recent user and assistant messages
    last_user_msg = conversation.messages.filter(role='user').order_by('-timestamp').first()
    last_assistant_msg = conversation.messages.filter(role='assistant').order_by('-timestamp').first()

    if last_user_msg and last_assistant_msg:
        previous_user_input = last_user_msg.content
        previous_response = last_assistant_msg.content
        # Check if the last assistant message was rated low (<4)
        if last_assistant_msg.rating is not None and last_assistant_msg.rating < 4:
            low_rating_flag = True

    # Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=user_input
    )

    # Get assistant response
    assistant_reply = services.ask_assistant(
        user_input=user_input,
        conversation_history=history_list,
        previous_user_input=previous_user_input,
        previous_response=previous_response,
        low_rating_flag=low_rating_flag,
        use_web_search=use_web_search
    )

    # Save assistant message (rating initially null)
    assistant_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=assistant_reply
    )
    return Response({
        'conversation_id': conversation.id,
        'user_message': MessageSerializer(user_message).data,
        'assistant_message': MessageSerializer(assistant_message).data
    })

@api_view(['POST'])
def rate_message(request):
    """Submit rating for an assistant message and store in ChromaDB."""
    message_id = request.data.get('message_id')
    rating = request.data.get('rating')

    if not message_id or rating is None:
        return Response({'error': 'message_id and rating required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        message = Message.objects.get(id=message_id, role='assistant')
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

    message.rating = rating
    message.save()

    # Also store in ChromaDB for RL memory
    # Find the preceding user message in the same conversation
    previous_user_msg = Message.objects.filter(
        conversation=message.conversation,
        role='user',
        timestamp__lt=message.timestamp
    ).order_by('-timestamp').first()

    if previous_user_msg:
        services.add_interaction(previous_user_msg.content, message.content, rating)

    return Response({'status': 'rated'})

@api_view(['GET'])
def history(request):
    """Get conversation history for the current session."""
    # Allow explicit conversation id in query params so frontend can fetch specific conversation
    conversation = get_or_create_conversation(request)
    messages = conversation.messages.order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def chat_stream(request):
    """Return assistant reply as a streaming chunked response.

    This uses the existing `services.ask_assistant` (non-streaming) and
    streams the final text in smaller chunks so the frontend can display
    incremental content. If a streaming-capable LLM is added later, this
    endpoint can be updated to proxy the real stream.
    """
    user_input = request.data.get('message', '').strip()
    use_web_search = request.data.get('use_web_search', True)

    if not user_input:
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    conversation = get_or_create_conversation(request)

    # Build history for context
    recent_messages = conversation.messages.order_by('-timestamp')[:10]
    history_messages = list(reversed(recent_messages))
    history_list = [{'role': m.role, 'content': m.content} for m in history_messages]

    # Determine previous user input and assistant response
    last_user_msg = conversation.messages.filter(role='user').order_by('-timestamp').first()
    last_assistant_msg = conversation.messages.filter(role='assistant').order_by('-timestamp').first()

    previous_user_input = last_user_msg.content if last_user_msg else None
    previous_response = last_assistant_msg.content if last_assistant_msg else None
    low_rating_flag = False
    if last_assistant_msg and last_assistant_msg.rating is not None and last_assistant_msg.rating < 4:
        low_rating_flag = True

    # Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=user_input
    )

    # Generate assistant reply synchronously
    assistant_reply = services.ask_assistant(
        user_input=user_input,
        conversation_history=history_list,
        previous_user_input=previous_user_input,
        previous_response=previous_response,
        low_rating_flag=low_rating_flag,
        use_web_search=use_web_search
    )

    # Save assistant message
    assistant_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=assistant_reply
    )

    # Stream the assistant_reply in chunks
    def stream_generator(text, chunk_size=256):
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]

    response = StreamingHttpResponse(stream_generator(assistant_reply), content_type='text/plain')
    response['X-Conversation-Id'] = str(conversation.id)
    return response


@api_view(['GET', 'POST'])
def conversations(request):
    """List or create conversations for the current session.

    GET: return recent conversations for the current session.
    POST: create a new conversation and return it.
    """
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.method == 'GET':
        convs = Conversation.objects.filter(session_key=session_key).order_by('-updated_at')
        serializer = ConversationSerializer(convs, many=True)
        return Response(serializer.data)

    # POST -> create conversation
    conv = Conversation.objects.create(session_key=session_key)
    serializer = ConversationSerializer(conv)
    return Response(serializer.data, status=status.HTTP_201_CREATED)