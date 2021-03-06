import logging
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, exc

from app.database import db
from app.event.models import Event

event = Blueprint('event', __name__, url_prefix='/events')

logger = logging.getLogger(__name__)


@event.route('/')
@event.route('/page/<int:page>')
@login_required
def index(page=1):

    LIMIT = 15
    user_id = current_user.get_id()
    events_ = Event.query.filter(
        and_(Event.status.__ne__(Event.STATUS_DELETE),
             Event.user_id.__eq__(user_id))).order_by(
        Event.date_at.asc()).paginate(
        page, LIMIT, False)

    if events_:
        for event in events_.items:
            for views_ in event.views:
                if not hasattr(event, 'cnt_views'):
                    event.cnt_views = 0

                event.cnt_views += views_.cnt

    return render_template('events.html', user=current_user, events=events_, title='Список событий')


@event.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    if request.method.__eq__('POST'):

        title = request.form.get('title')
        date_at = request.form.get('date_at')
        place = request.form.get('place')

        if title is not None and len(title) > 0:
            title = title.strip()

        if date_at is not None and len(date_at) > 0:
            date_at = datetime.strptime(date_at, '%d.%m.%Y')

        if place is not None and len(place) > 0:
            place = place.strip()

        if title and date_at and place:

            try:
                event_ = Event(
                    title=title,
                    date_at=date_at,
                    place=place,
                    status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    user_id=current_user.get_id()
                )

                db.session.add(event_)
                db.session.commit()

            except exc.IntegrityError as ex:

                logger.exception(ex)
                db.session.rollback()

                flash('Что то пошло не так!!!')

            return redirect(url_for('.index'))
        else:
            flash('Данные не прошли проверку!!!')

    return render_template('event-create.html', title="Создание события")


@event.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit(id):
    user_id = current_user.get_id()
    event_ = Event.query.filter(and_(Event.id.__eq__(id), Event.user_id.__eq__(user_id))).first()

    if request.method.__eq__('POST'):

        title = request.form.get('title')
        date_at = request.form.get('date_at')
        place = request.form.get('place')

        if title is not None and len(title) > 0:
            title = title.strip()

        if date_at is not None and len(date_at) > 0:
            date_at = datetime.strptime(date_at, '%d.%m.%Y')

        if place is not None and len(place) > 0:
            place = place.strip()

        if title and date_at and place:

            event_.title = title
            event_.date_at = date_at
            event_.place = place
            event_.updated_at = datetime.now()

            db.session.add(event_)
            db.session.commit()

            return redirect(url_for('.index'))

        else:
            flash('Данные не прошли проверку!!!')

    return render_template('event-edit.html', event=event_, title=f'Редактирование события № {id}')


@event.route('/delete/<int:id>')
@login_required
def delete(id):
    if id:
        try:

            id = int(id)
            user_id = current_user.get_id()

            event_ = Event.query.filter(and_(Event.id.__eq__(id), Event.user_id.__eq__(user_id))).first()
            if event_ is not None:
                event_.status = Event.STATUS_DELETE
                event_.updated_at = datetime.now()

                db.session.add(event_)
                db.session.commit()

                flash(f'Успешное удаление события № {id}')

                return redirect(url_for('event.index'))

        except (TypeError, ValueError) as ex:
            logger.exception(ex)
            flash('При удалении произошла ошибка!!!')
            return redirect(url_for('event.index'))

    flash('При удалении произошла ошибка!!!')
    return redirect(url_for('event.index'))
