import os
from datetime import datetime

import sqlite3
from sqlite3 import Error

from flask import render_template
from flask import request
from flask import Flask

app = Flask(__name__)
from trustify import Keystream


@app.route('/')
def home():
    """Renders the home page."""
    try:
        rlc_params = request.args.get('rlc')
        if len(rlc_params) != 32:
            rlc_params = None
    except:
        rlc_params = None
        
    if  rlc_params is None:
        return render_template(
                                'index.html',
                                title = 'SIC43NT Demonstration',
                                uid = 'N/A',
                                key = 'N/A',
                                flag_tamper = 'N/A',
                                flag_tamper_from_server = 'N/A',
                                flag_tamper_decision = 'N/A',

                                time_stamp_int = 'N/A',
                                time_stamp_from_server = 'N/A',
                                time_stamp_decision = 'N/A',

                                rolling_code = 'N/A',
                                rolling_code_from_server = 'N/A',
                                rolling_code_decision = 'N/A'
                            )
    else:
        #### GET PARAMS ####
        tag_uid = rlc_params[0:14]
        tag_key = 'FFFFFF' + tag_uid
        tag_flag_tamper = rlc_params[14:16]
        tag_time_stamp = rlc_params[16:24]
        tag_time_stamp_int = int(tag_time_stamp, 16)
        tag_rolling_code = rlc_params[24:32]

        keystream = Keystream()
        server_rolling_code = keystream.stream(tag_key, tag_time_stamp, 4).upper()
        
        print("server_rolling_code:",server_rolling_code)

        #### QUERY BY UID ####
        try:
            conn = sqlite3.connect('trustify.db')
            cur = conn.cursor()
            cur.execute("SELECT * FROM ntstorage WHERE UID=?", (tag_uid,))
            [server_uid, server_key, server_time_stamp, rlccc] = cur.fetchone()
            server_time_stamp_int = int(server_time_stamp)
        except:
            return render_template(
                                    'index.html',
                                    title = 'SIC43NT Demonstration',
                                    uid = 'N/A',
                                    key = 'N/A',
                                    flag_tamper = 'N/A',
                                    flag_tamper_from_server = 'N/A',
                                    flag_tamper_decision = 'N/A',

                                    time_stamp_int = 'N/A',
                                    time_stamp_from_server = 'N/A',
                                    time_stamp_decision = 'N/A',

                                    rolling_code = 'N/A',
                                    rolling_code_from_server = 'N/A',
                                    rolling_code_decision = 'N/A'
                                )

        #### COMPARE ROLLING CODE ####
        if tag_rolling_code == server_rolling_code:
            rolling_code_decision = 'Correct!!'
        else:
            rolling_code_decision = 'Incorrect...'

        #### COMPARE TIMESTAMP ####
        if tag_time_stamp_int > server_time_stamp_int:
            time_stamp_decision = 'Correct!!'
        else:
            time_stamp_decision = 'Incorrect...'


        return render_template(
                                'index.html',
                                title = 'SIC43NT Demonstration',
                                uid = tag_uid,
                                key = tag_key,
                                flag_tamper = tag_flag_tamper,
                                flag_tamper_from_server = 'N/A',
                                flag_tamper_decision = 'N/A',

                                time_stamp_int = tag_time_stamp_int,
                                time_stamp_from_server = server_time_stamp_int,
                                time_stamp_decision = time_stamp_decision,

                                rolling_code = tag_rolling_code,
                                rolling_code_from_server = server_rolling_code,
                                rolling_code_decision = rolling_code_decision
                            )

@app.route('/add')
def contact():
    """Renders the add page."""
    try:
        uid_params = request.args.get('uid')
        if len(uid_params) != 14:
            uid_params = None
        key_params = request.args.get('key')
        if len(key_params) != 20:
            key_params = None
    except:
        uid_params = None
        key_params = None
    
    if uid_params is None or key_params is None:    
        return render_template(
            'add.html',
            title='Add',
            uid = 'Need UID: 14',
            key = 'Need Key: 20'
        )
    else:
        try:
            conn = sqlite3.connect('trustify.db')
            c = conn.cursor()
            c.execute("INSERT INTO ntstorage (UID, Key, TimeStamp, RollingCode) VALUES (?,?,?,?)",
                        (uid_params.upper(), key_params.upper(), -1, '0'))
            conn.commit()
            conn.close()
        except:
            uid_params = 'may be conflict?'
            key_params = 'wrong pattern'

        return render_template(
                'add.html',
                title='Add',
                uid = uid_params.upper(),
                key = key_params.upper()
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
