from botbuilder.core import ActivityHandler

from services.dialog_service import handle_chat_message


class RegistrationBot(ActivityHandler):

    async def on_message_activity(self, turn_context):

        session_id = turn_context.activity.from_property.id

        message = turn_context.activity.text

        result = handle_chat_message(
            session_id,
            message
        )

        await turn_context.send_activity(
            result["reply"]
        )