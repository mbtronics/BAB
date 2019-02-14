from models.accessmodels import Lock
from flask import abort, current_app, jsonify, request
from flask.views import MethodView
from models.usermodels import User


class BASApi(MethodView):

    def post(self):
        if not request.json:
            abort(400)

        key = request.json.get('key')
        lock_id = request.json.get('lock_id')
        keycard = request.json.get('keycard')

        if not key or not lock_id or not keycard:
            abort(400)

        if key != current_app.config['LOCKS_KEY']:
            return jsonify({"error": "invalid key"}), 404

        user = User.query.filter_by(keycard=int(keycard)).first()
        if not user:
            return jsonify({"error": "invalid keycard"}), 404

        lock = Lock.query.get(lock_id)
        if not lock:
            return jsonify({"error": "invalid lock_id"}), 404

        if lock in user.locks.all():
            return jsonify({"result": "ok"}), 200

        return jsonify({"result": "access denied"}), 403
