from app import db


class Setting(db.Model):
    __tablename__ = 'Settings'
    name = db.Column(db.String(50), nullable=False, primary_key=True)
    value = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return self.value
