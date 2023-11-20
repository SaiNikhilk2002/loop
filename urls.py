from flask import Blueprint

from views import ManageChatView, ManageLoopView

loop_blueprint = Blueprint("loop", __name__, url_prefix="/loop")

loop_blueprint.add_url_rule(
    "",
    view_func=ManageLoopView.as_view("manage_loop"),
    methods=["GET", "POST", "PATCH", "DELETE"],
)

loop_blueprint.add_url_rule(
    "/chats",
    view_func=ManageChatView.as_view("manage_chat"),
    methods=["GET","POST","PATCH","DELETE"],
)
