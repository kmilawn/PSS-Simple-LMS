from mongoengine import connect

connect(
    db="simple_lms_logs",
    host="mongodb",
    port=27017
)