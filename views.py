import traceback
from bson import ObjectId
from flask import request, jsonify, make_response
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from collections import ChainMap

from pymongo import results
from settings import bucket_name, db_client, s3_client
from handlers import LoopHandler,ChatHandler
from utils import add_user_info


class ManageLoopView(MethodView):

    @jwt_required()
    def get(self):
        try:
            query_params = request.args
            user_id = ObjectId(get_jwt_identity())

            userId = query_params.get("userId")     
            if userId:
                ui = db_client.Users.find_one({"_id": ObjectId(userId), "status": "ACTIVE"}, {"accessibility": 1})
                if ui.get("accessibility") == "PRIVATE":
                    resp = {"message": "You can't access this profile"}
                    response_code = 500
                else:
                    user_id = ObjectId(userId)
                    response = LoopHandler().get_loop_users(user_id, query_params)
                    response_code = 200                   
                   
            else:
                response = LoopHandler().get_loop_users(user_id, query_params)
                response_code = 200

            if response.get("data"):
                user_ids = [] 
                for user in response["data"]:
                    user_ids.append(user["loopuser"])
                resp =list(db_client.Users.find(
                    {
                        "_id": {"$in": list(map(ObjectId, user_ids))}
                    }, {"name": 1, "profile_Name": 1, "key": 1, "bio": 1}
                ))
                
                looped_user_ids = [x["loopuser"] for x in response["data"]]
                print(looped_user_ids)
                
                for x in resp:
                    x["_id"] = str(x["_id"])
                    x["key"] = str(x["key"])
                    x["url"] = f"https://{bucket_name}.s3.amazonaws.com/{x['key']}"
                    if str(x["_id"]) in looped_user_ids:
                        x["loop_status"] = "looped"
                    else:
                        x["loop_status"] = "not looped"

                response_code = 200 

                limit = int(query_params.get("limit") or 20)
                next_page = None
                if len(resp) > limit:
                    next_page = {"offset": limit, "limit": limit}
                    resp = resp[:limit]
 
                response = {"data": resp, "next_page": next_page}
                response["statusCode"] = response_code

                return make_response(jsonify(response), response_code)

        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to fetch loop users."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            user_id = ObjectId(get_jwt_identity())
            response, response_code = LoopHandler().send_loop_request(user_id, ObjectId(data["sentForUserId"]))

        except Exception as e:
            traceback.print_exc()
            response = {"message": "Unable to send loop request. Exception: {}".format(str(e))}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)
    
    @jwt_required()
    def patch(self):
        try:

            data = request.get_json()
            user_id = ObjectId(get_jwt_identity())
            response, response_code = LoopHandler().accept_or_reject_loop_request(ObjectId(data["sentByUserId"]), user_id, data["status"])

        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to update loop request."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)

    @jwt_required()
    def delete(self):
        try:
            query_params = request.args
            user_id = ObjectId(get_jwt_identity())
            if query_params.get("looping"):
                looping_user=ObjectId(query_params["looping"])
                response, response_code = LoopHandler().unloop_looping_user(user_id, looping_user)
            elif query_params.get("looper"):
                looper_user=ObjectId(query_params["looper"])
                response, response_code = LoopHandler().unloop_looper_user(user_id, looper_user)
                        

        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to unloop user."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)


class ManageChatView(MethodView):

    @add_user_info
    @jwt_required()
    def get(self):
        try:
            query_params = request.args
            request_user_id = ObjectId(get_jwt_identity())
            response = ChatHandler().fetch_chats(request_user_id, query_params)
            response_code = 200

        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to fetch chats."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)

    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            createdBy= ObjectId(get_jwt_identity())
            response = ChatHandler().chat_post_request(createdBy, data["CreatedFor"],data["status"])
            response_code = 200

        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to send request."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)
    
    @jwt_required()
    def patch(self):
        try:
            data = request.get_json()
            createdBy= ObjectId(get_jwt_identity())
            response, response_code= ChatHandler().chat_respond_request(createdBy, data["CreatedFor"],data["status"])
            
        except Exception:
            traceback.print_exc()
            response = {"message": "Unable to accept/reject request."}
            response_code = 500

        response["statusCode"] = response_code
        return make_response(jsonify(response), response_code)

    # @jwt_required()
    # def get(self):
    #     try:
    #         data = request.get_json()
    #         senderUserId= ObjectId(get_jwt_identity())
    #         response = ChatHandler().chat_status(senderUserId, data["senderForUserId"])
    #         response_code = 200

    #     except Exception:
    #         traceback.print_exc()
    #         response = {"message": "Unable to show connection status."}
    #         response_code = 500

    #     response["statusCode"] = response_code
    #     return make_response(jsonify(response), response_code)



