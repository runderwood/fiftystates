import datetime

metadata = dict(
    name='Massachusetts',
    abbreviation='ma',
    legislature_name='Massachusetts General Court',
    upper_chamber_name='Senate',
    lower_chamber_name='House of Representatives',
    upper_chamber_title='Senator',
    lower_chamber_title='Representative',
    upper_chamber_term=2,
    lower_chamber_term=2,
    terms=[
        {'name': '186',
         'sessions': ['186'],
         'start_year': 2009, 'end_year': 2010},
        ],
    session_details={
        '186.2009': {'start_date': datetime.date(2009, 1, 7),
               'end_date': datetime.date(2010, 1, 1)},
        '186.2010': {'start_date': datetime.date(2010, 1, 6),
                'end_Date': datetime.date(2011, 1, 1)},
        },
    )
