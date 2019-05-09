import os
from datetime import datetime

import sqlite3
from sqlite3 import Error

from flask import render_template
from flask import request
from flask import Flask

app = Flask(__name__)
from trustify import Keystream


@app.route('/', methods=['GET'])
def home():
    """Renders the home page."""
    rlc_params = request.args.get('rlc')
    if not rlc_params or len(rlc_params) != 32:
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
        """
        Preraring Params
        
        1: Get params from URL
        2: Get params from Database
        """
        ####---- From URL ----####
        tag_uid = rlc_params[0:14]
        tag_flag_tamper = rlc_params[14:16]
        tag_time_stamp = rlc_params[16:24]
        tag_time_stamp_int = int(tag_time_stamp, 16)
        tag_rolling_code = rlc_params[24:32]

        ####---- From Database ----####
        server_key = None
        
        conn = sqlite3.connect('trustify.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM ntstorage WHERE UID=?", (tag_uid,))
        [server_uid, server_key, server_time_stamp, previous_rolling_code] = cur.fetchone()
        server_time_stamp_int = int(server_time_stamp)

        keystream = Keystream()
        server_rolling_code = keystream.stream(server_key, tag_time_stamp, 4).upper()
        
        print("server_rolling_code:",server_rolling_code)

        """
        Trustify agreement check
        
        1: Compare timestamp (tag VS server)
        2: Compare Rolling Code (tag VS server)
        """
        #### COMPARE TIMESTAMP ####
        if tag_time_stamp_int > server_time_stamp_int:
            time_stamp_decision = 'Rolling Code Updated!!'

            conn = sqlite3.connect('trustify.db')
            cur = conn.cursor()
            cur.execute("UPDATE ntstorage SET TimeStamp=? WHERE UID=?", (tag_time_stamp_int,tag_uid))
            conn.commit()
        else:
            time_stamp_decision = 'Rolling Code Reused!!'

        #### COMPARE ROLLING CODE ####
        if tag_rolling_code == server_rolling_code:
            rolling_code_decision = 'Correct!!'
        else:
            rolling_code_decision = 'Incorrect...'   

            
        return render_template(
                                'index.html',
                                title = 'SIC43NT Demonstration',
                                uid = tag_uid,
                                key = server_key,
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
    return render_template("add.html")

@app.route('/', methods=['POST'])
def added():  
    try:
        uid_params = request.form['uid'].upper()
        if len(uid_params) != 14:
            uid_params = None

        key_params = request.form['key'].upper()
        if len(key_params) != 20:
            key_params = None

    except:
        uid_params = None
        key_params = None

    if uid_params is None or key_params is None:    
        return render_template('result.html',
            head = 'SIC43NT Add UID Failure..',
            uid = 'Need UID: 14 chars',
            key = 'Need Key: 20 chars'
        )
    else:
        conn = sqlite3.connect('trustify.db')
        c = conn.cursor()
        try:
            #### ADD UID ####
            c.execute("INSERT INTO ntstorage (UID, Key, TimeStamp, RollingCode) VALUES (?,?,?,?)",
                        (uid_params, key_params, -1, '0'))
            conn.commit()
            conn.close()
            head_params = 'SIC43NT Add UID Successful!!'
        except Error as ee:
            #### UPDATE UID ####
            if 'UNIQUE' in str(ee):
                c.execute("UPDATE ntstorage SET Key=? WHERE UID=?", (key_params,uid_params))
                conn.commit()
                conn.close()
                head_params = 'SIC43NT Update UID or Key Successful!!'
            else:
                head_params = 'SIC43NT Add UID Failure..',
                uid_params = 'wrong pattern'
                key_params = 'wrong pattern'

        return render_template("result.html",
                head = head_params,
                uid = uid_params,
                key = key_params
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
