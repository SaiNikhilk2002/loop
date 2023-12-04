from bson import ObjectId
from datetime import datetime

from pymongo import results

from settings import db_client


class LoopHandler:

    def get_loop_users(self, user_id, query_params):

        offset = int(query_params.get("offset") or 0)
        limit = int(query_params.get("limit") or 20)
        name_search = query_params.get("name")
        loop_type=query_params.get("loop_type")
        
        query = {
            "$and": [
                {
                    "$or": [
                        {"createdBy": user_id},
                        {"createdFor": user_id},
                    ],
                },
                {"status": "ACCEPTED"}
            ]
        }

        projection = {
            "_id": 0,
            "createdFor": 1,
            "createdBy": 1,
        }
        
        if name_search:
            name_search = name_search.lower().strip()
            query["$and"].append(
                {
                    "$or": [
                        {"createdByName": {"$regex": name_search}},
                        {"createdForName": {"$regex": name_search}},
                    ],
                }
            )
            
        if loop_type:
            if loop_type=="looping":
                query["$and"].append(
                    { "createdBy": user_id}
                )
            else:
                query["$and"].append(
                    { "createdFor": user_id}
                )

        loop_requests = list(
            db_client.LoopRequests.find(query, projection=projection).sort("updatedOn", -1).skip(offset).limit(limit+1)
        )
        
        next_page = None
        if len(loop_requests) > limit:
            next_page = {"offset": offset + limit, "limit": limit}
            loop_requests = loop_requests[:-1]  # remove the extra doc fetched

        created_for_ids = [loop_request["createdFor"] for loop_request in loop_requests if loop_request["createdFor"] != user_id]
        existing_loop_request_status_map = {
            loop_request["createdFor"]: loop_request["status"]
            for loop_request in list(
                db_client.LoopRequests.find(
                    {
                        "createdBy": user_id,
                        "createdFor": {"$in": created_for_ids},
                        "status": "ACCEPTED",
                    }
                )
            ) or []
        } if created_for_ids else {}
       
        for loop_request in loop_requests:
            # loop_request["status"] = existing_loop_request_status_map.get(loop_request["createdFor"]) or "NOT_FOUND"
            
            if existing_loop_request_status_map.get(loop_request["createdFor"]):
                loop_request["loopuser"] = str(loop_request["createdFor"])
            
            else:
                loop_request["loopuser"] = str(loop_request["createdBy"])
            
            loop_request.pop("createdFor")
            loop_request.pop("createdBy")
        
        response = {
            "data": loop_requests,
            "nextPage": next_page
        }
        return response  


    # def send_loop_request(self, sent_by_user_id, sent_for_user_id):

    #     sent_for_user_doc = db_client.Users.find_one({"_id": sent_for_user_id})
    #     if (
    #         "sent_by_user_id" in sent_for_user_doc.get("blockedUserIds", [])
    #         or "sent_by_user_id" in sent_for_user_doc.get("blockedByUserIds", [])
    #     ):
    #         response = {"message": "You can't send a loop request to this user."}
    #         response_code = 403
            
    #     else:
    #         existing_request = db_client.LoopRequests.find_one(
    #             {
    #                 "createdBy": sent_by_user_id,
    #                 "createdFor": sent_for_user_id
    #             }
    #         )

    #         if existing_request and existing_request.get("status") == "PENDING":
    #             response = {"message": "You already have a pending loop request."}
    #             response_code = 400

    #         elif existing_request and existing_request.get("status") == "ACCEPTED":
    #             response = {"message": "This user is already in your loop."}
    #             response_code = 200
            
    #         elif existing_request and existing_request.get("status") in ["INACTIVE", "REJECTED"]:
    #             db_client.LoopRequests.update_one(
    #                 {"_id": existing_request["_id"]},
    #                 {
    #                     "$set": {
    #                         "status": "PENDING",
    #                         "updatedBy": sent_by_user_id,
    #                         "updatedOn": datetime.now()
    #                     }
    #                 }
    #             )
    #             msg=db_client.NotificationContent.find_one({"_id":ObjectId("61c48cd7af2d65aa18e5c5d1")},{"_id":0,"msg":1})
    #             db_client.Notifications.insert_one({
    #                 "status": "UNREAD",
    #                 "notification": msg["msg"],
    #                 "type": "loop",
    #                 "key": sent_by_user_doc["key"],
    #                 "senderId": sent_by_user_id,
    #                 "receiverId": sent_for_user_id,
    #                 "senderName": sent_by_user_doc["name"],
    #                 "reactionType": None,
    #                 "createdOn": datetime.now()
    #             })
    #             response = {"message": "Loop request sent."}
    #             response_code = 200

    #         else:
    #             if sent_for_user_doc.get("accessibility") == "PRIVATE":
    #                 time_now = datetime.now()
    #                 sent_by_user_doc = db_client.Users.find_one({"_id": sent_by_user_id})
    #                 db_client.LoopRequests.insert_one(
    #                     {
    #                         "createdBy": sent_by_user_id,
    #                         "createdByName": sent_by_user_doc["name"].lower(),
    #                         "createdFor": sent_for_user_id,
    #                         "createdForName": sent_for_user_doc["name"].lower(),
    #                         "createdOn": time_now,
    #                         "updatedOn": time_now,
    #                         "status": "PENDING"
    #                     }
    #                 )
    #                 msg=db_client.NotificationContent.find_one({"_id":ObjectId("61c48cd7af2d65aa18e5c5d1")},{"_id":0,"msg":1})
    #                 db_client.Notifications.insert_one({
    #                 "status": "UNREAD",
    #                 "notification": msg["msg"],
    #                 "type": "loop",
    #                 "key":sent_by_user_doc["key"],
    #                 "senderId": sent_by_user_id,
    #                 "receiverId": sent_for_user_id,
    #                 "senderName": sent_by_user_doc["name"],
    #                 "reactionType": None,
    #                 # "senderName": sent_by_user_doc["name"],
    #                 "createdOn": datetime.now()
    #             })
    #                 response = {"message": "Loop request sent."}
    #                 response_code = 200
    #             elif sent_for_user_doc.get("accessibility") == "PUBLIC":
    #                 time_now = datetime.now()
    #                 sent_by_user_doc = db_client.Users.find_one({"_id": sent_by_user_id})
    #                 db_client.LoopRequests.insert_one(
    #                     {
    #                         "createdBy": sent_by_user_id,
    #                         "createdByName": sent_by_user_doc["name"].lower(),
    #                         "createdFor": sent_for_user_id,
    #                         "createdForName": sent_for_user_doc["name"].lower(),
    #                         "createdOn": time_now,
    #                         "updatedOn": time_now,
    #                         "status": "ACCEPTED"
    #                     }
    #                 )
    #                 msg=db_client.NotificationContent.find_one({"_id":ObjectId("61c48d2aaf2d65aa18e5c5d2")},{"_id":0,"msg":1})
    #                 db_client.Notifications.insert_one({
    #                 "status": "UNREAD",
    #                 "notification": msg["msg"],
    #                 "reactionType": None,
    #                 "type": "loop",
    #                 "key":sent_by_user_doc["key"],
    #                 "senderId": sent_by_user_id,
    #                 "receiverId": sent_for_user_id,
    #                 "senderName": sent_by_user_doc["name"],
    #                 "createdOn": datetime.now()
    #             })
    #                 response = {"message": "looped successfully.."}
    #                 response_code = 200

    #     return response, response_code
    
    def send_loop_request(self, sent_by_user_id, sent_for_user_id):
        sent_for_user_doc = db_client.Users.find_one({"_id": sent_for_user_id})

        if sent_for_user_doc:
            if (
                "sent_by_user_id" in sent_for_user_doc.get("blockedUserIds", [])
                or "sent_by_user_id" in sent_for_user_doc.get("blockedByUserIds", [])
            ):
                response = {"message": "You can't send a loop request to this user."}
                response_code = 403
            else:
                existing_request = db_client.LoopRequests.find_one(
                    {
                        "createdBy": sent_by_user_id,
                        "createdFor": sent_for_user_id
                    }
                )

                if existing_request and existing_request.get("status") == "PENDING":
                    response = {"message": "You already have a pending loop request."}
                    response_code = 400
                elif existing_request and existing_request.get("status") == "ACCEPTED":
                    response = {"message": "This user is already in your loop."}
                    response_code = 200
                elif existing_request and existing_request.get("status") in ["INACTIVE", "REJECTED"]:
                    db_client.LoopRequests.update_one(
                        {"_id": existing_request["_id"]},
                        {
                            "$set": {
                                "status": "PENDING",
                                "updatedBy": sent_by_user_id,
                                "updatedOn": datetime.now()
                            }
                        }
                    )
                    msg = db_client.NotificationContent.find_one({"_id": ObjectId("61c48cd7af2d65aa18e5c5d1")}, {"_id": 0, "msg": 1})
                    db_client.Notifications.insert_one({
                        "status": "UNREAD",
                        "notification": msg["msg"],
                        "type": "loop",
                        "key": sent_by_user_doc["key"],
                        "senderId": sent_by_user_id,
                        "receiverId": sent_for_user_id,
                        "senderName": sent_by_user_doc["name"],
                        "reactionType": None,
                        "createdOn": datetime.now()
                    })
                    response = {"message": "Loop request sent."}
                    response_code = 200
                else:
                    if sent_for_user_doc.get("accessibility") == "PRIVATE":
                        time_now = datetime.now()
                        sent_by_user_doc = db_client.Users.find_one({"_id": sent_by_user_id})
                        db_client.LoopRequests.insert_one(
                            {
                                "createdBy": sent_by_user_id,
                                "createdByName": sent_by_user_doc["name"].lower(),
                                "createdFor": sent_for_user_id,
                                "createdForName": sent_by_user_doc["name"].lower(),
                                "createdOn": time_now,
                                "updatedOn": time_now,
                                "status": "PENDING"
                            }
                        )
                        msg = db_client.NotificationContent.find_one({"_id": ObjectId("61c48cd7af2d65aa18e5c5d1")}, {"_id": 0, "msg": 1})
                        db_client.Notifications.insert_one({
                            "status": "UNREAD",
                            "notification": msg["msg"],
                            "type": "loop",
                            "key": sent_by_user_doc["key"],
                            "senderId": sent_by_user_id,
                            "receiverId": sent_for_user_id,
                            "senderName": sent_by_user_doc["name"],
                            "reactionType": None,
                            "createdOn": datetime.now()
                        })
                        response = {"message": "Loop request sent."}
                        response_code = 200
                    elif sent_for_user_doc.get("accessibility") == "PUBLIC":
                        time_now = datetime.now()
                        sent_by_user_doc = db_client.Users.find_one({"_id": sent_by_user_id})
                        db_client.LoopRequests.insert_one(
                            {
                                "createdBy": sent_by_user_id,
                                "createdByName": sent_by_user_doc["name"].lower(),
                                "createdFor": sent_for_user_id,
                                "createdForName": sent_by_user_doc["name"].lower(),
                                "createdOn": time_now,
                                "updatedOn": time_now,
                                "status": "ACCEPTED"
                            }
                        )
                        msg = db_client.NotificationContent.find_one({"_id": ObjectId("61c48d2aaf2d65aa18e5c5d2")}, {"_id": 0, "msg": 1})
                        db_client.Notifications.insert_one({
                            "status": "UNREAD",
                            "notification": msg["msg"],
                            "reactionType": None,
                            "type": "loop",
                            "key": sent_by_user_doc["key"],
                            "senderId": sent_by_user_id,
                            "receiverId": sent_for_user_id,
                            "senderName": sent_by_user_doc["name"],
                            "createdOn": datetime.now()
                        })
                        response = {"message": "Looped successfully."}
                        response_code = 200

        else:
            response = {"message": "User not found with the specified _id."}
            response_code = 404

        return response, response_code

    def accept_or_reject_loop_request(self, sent_by_user_id, sent_for_user_id, status="ACCEPTED"):
        sent_by_user_doc = db_client.Users.find_one({"_id": sent_by_user_id},{"_id":0,"name":1})

        if status not in ["ACCEPTED", "REJECTED"]:
            raise Exception

        existing_request = db_client.LoopRequests.find_one(
            {
                "createdBy": sent_by_user_id,
                "createdFor": sent_for_user_id,
                "status": "PENDING",
            }
        )

        if existing_request:
            db_client.LoopRequests.update_one(
                {"_id": existing_request["_id"]},
                {
                    "$set": {
                        "status": status,
                        "updatedBy": sent_for_user_id,
                        "updatedOn": datetime.now()
                    }
                }
            )
            if status=="ACCEPTED":
                msg=db_client.NotificationContent.find_one({"_id":ObjectId("61c48d3faf2d65aa18e5c5d3")},{"_id":0,"msg":1})
                db_client.Notifications.insert_one({
                    "status": "UNREAD",
                    "notification": msg["msg"],
                    "type": "loop",
                    "key":sent_by_user_id["key"],
                    "senderId": sent_by_user_id,
                    "receiverId": sent_for_user_id,
                    "reactionType": None,
                    "senderName": sent_by_user_doc["name"],

                    "createdOn": datetime.now()#sender name
                }) 
            else:
                msg=db_client.NotificationContent.find_one({"_id":ObjectId("61c48d7aaf2d65aa18e5c5d4")},{"_id":0,"msg":1})
                db_client.Notifications.insert_one({
                    "status": "UNREAD",
                    "notification": msg["msg"],
                    "type": "loop",
                    "key":sent_by_user_id["key"],
                    "senderId": sent_by_user_id,
                    "receiverId": sent_for_user_id,
                    "reactionType": None,
                    "senderName": sent_by_user_doc["name"],

                    "createdOn": datetime.now()#sender name
                })  
            response = {"message": "Loop request {status}.".format(status=status.lower())}
            response_code = 400
        
        else:
            response = {"message": "No pending loop request found."}
            response_code = 400
            

        return response, response_code

    def unloop_looping_user(self, user_id, looping_user):
        looping_query = db_client.LoopRequests.find_one(
            {
                "createdBy": user_id,
                "createdFor": looping_user,
                "status": "ACCEPTED"
            }
        )

        if looping_query:
            db_client.LoopRequests.update_one(
                {"_id": looping_query["_id"]},
                {
                    "$set": {
                        "status": "INACTIVE",
                        "updatedBy": user_id,
                        "updatedOn": datetime.now()
                    }
                }
            )
            response = {"message": "The loop user was removed from looping."}
            response_code = 400

        else:
            response = {"message": "No accepted loop request found."}
            response_code = 400
        
        return response, response_code

    def unloop_looper_user(self, user_id, looper_user):
        
        looper_query = db_client.LoopRequests.find_one(
            {
                "createdFor": user_id,
                "createdBy": looper_user,
                "status": "ACCEPTED"
            }
        )

        if looper_query:
            db_client.LoopRequests.update_one(
                {"_id": looper_query["_id"]},
                {
                    "$set": {
                        "status": "INACTIVE",
                        "updatedBy": user_id,
                        "updatedOn": datetime.now()
                    }
                }
            )
            response = {"message": "The loop user was removed from loopers."}
            response_code = 200

        else:
            response = {"message": "No accepted loop request found."}
            response_code = 200
        
        return response, response_code


    # def fetch_chats(self, request_user_id, query_params):

    #     user_id = ObjectId(query_params["userId"])
    #     offset = int(query_params.get("offset") or 0)
    #     limit = int(query_params.get("limit") or 20)

    #     query = {
    #         "$or": [
    #             {"createdBy": request_user_id, "createdFor": user_id},
    #             {"createdBy": user_id, "createdFor": request_user_id},
    #         ],
    #     }

    #     chats = list(
    #         db_client.ChatMessages.find(query).sort("createdOn", -1).skip(offset).limit(limit+1)
    #     )

    #     next_page = None
    #     if len(chats) > limit:
    #         next_page = {"offset": offset + limit, "limit": limit}
    #         chats = chats[:-1]  # remove the extra doc fetched

    #     for chat in chats:
    #         chat["id"] = str(chat.pop("_id"))
    #         chat["createdBy"] = str(chat["createdBy"])
    #         chat["createdFor"] = str(chat["createdFor"])
    #         chat["message"]=str(chat["message"].decode('utf-8'))

    #     response = {
    #         "data": chats,
    #         "nextPage": next_page
    #     }
    #     return response

class ChatHandler:

    def fetch_chats(self, request_user_id, query_params):

        user_id = ObjectId(query_params["userId"])
        offset = int(query_params.get("offset") or 0)
        limit = int(query_params.get("limit") or 20)

        query = {
            "$or": [
                {"createdBy": request_user_id, "createdFor": user_id},
                {"createdBy": user_id, "createdFor": request_user_id},
            ],
        }

        chats = list(
            db_client.ChatMessages.find(query).sort("createdOn", -1).skip(offset).limit(limit+1)
        )
        next_page = None
        if len(chats) > limit:
            next_page = {"offset": offset + limit, "limit": limit}
            chats = chats[:-1]  # remove the extra doc fetched

        for chat in chats:
            chat["id"] = str(chat.pop("_id"))
            chat["createdBy"] = str(chat["createdBy"])
            chat["createdFor"] = str(chat["createdFor"])
            chat["message"]=str(chat["message"].decode('utf-8'))

        response = {
            "data": chats,
            "nextPage": next_page
        }
        return response
    
    def chat_post_request(self,createdBy,CreatedFor,status):

        Created_For = db_client.Users.find_one({"_id": createdBy})
        if (
            createdBy in Created_For.get("blockedUserIds", [])
            or createdBy in Created_For.get("blockedByUserIds", [])
        ):
            response = {"message": "You can't send a message request to this user."}
            response_code = 403
            
        else:
            existing_request = db_client.ChatRequests.find_one(
                {
                    "createdBy": createdBy,
                    "createdFor": CreatedFor
                }
            )

            if existing_request and existing_request.get("status") == "PENDING":
                response = {"message": "You already have a pending chat request."}
                response_code = 400

            elif existing_request and existing_request.get("status") == "ACCEPTED":
                response = {"message": "This user is already in your chat connections."}
                response_code = 400
            
            elif existing_request and existing_request.get("status") in ["INACTIVE", "REJECTED"]:
                db_client.LoopRequests.update_one(
                    {"_id": existing_request["_id"]},
                    {
                        "$set": {
                            "status": "PENDING",
                            "updatedBy": createdBy,
                            "updatedOn": datetime.now()
                        }
                    }
                )
                response = {"message": "chat request sent."}
                response_code = 200
            
        return response, response_code


    def chat_respond_request(self,createdBy,CreatedFor,status):
        
        if status not in ["ACCEPTED", "REJECTED"]:
            raise Exception

        existing_request = db_client.ChatConnections.find_one(
            {"$or":[
            {
                "receiverUserId": createdBy,
                "senderuserId": ObjectId(CreatedFor),
                "status": "REQUESTED",
            },
            {
                "receiverUserId": ObjectId(CreatedFor),
                "senderuserId": createdBy,
                "status": "REQUESTED",
            }
            ]}
        )

        if existing_request:
            db_client.ChatConnections.update_one(
                {"_id": existing_request["_id"]},
                {
                    "$set": {
                        "status": status,
                        "updatedBy": createdBy,
                        "updatedOn": datetime.now()
                    }
                }
            )
            response = {"message": "chat request {status}.".format(status=status.lower())}
            response_code = 200
        
        else:
            response = {"message": "No pending chat request found."}
            response_code = 404
            

        return response, response_code

        


    # def chat_status(self,senderUserId,senderForUserId):








