from flask import render_template
from . import main

@main.route('/info/skills')
def info_skills():
    return render_template('info/skills.html')