#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from turret import *

import json as _json
import threading as _threading

class Demo(Application):
    def __init__(self, home_dir, files_dir):
        super().__init__(home_dir, files_dir)

        self.model = Model(self)

class Model:
    def __init__(self, app):
        self.app = app

        self.issues_by_id = dict()

        self.lock = _threading.Lock()

class Issue:
    def __init__(self, model, id):
        self.model = model

        self.id = id
        self.summary = None
        self.description = None
        self.keywords = None

        assert self.id not in self.model.issues_by_id
        
        self.model.issues_by_id[self.id] = self
        
class CreateIssue(Procedure):
    def __init__(self, app, name):
        super().__init__(app, name)

        self.summary = StringParameter(self, "summary")
        self.description = StringParameter(self, "description")
        self.keywords = StringParameter(self, "keywords")
        self.redirect = StringParameter(self, "redirect")
        
    def do_process(self, request):
        summary = self.summary.get(request)
        description = self.description.get(request)
        keywords = self.keywords.get(request)
        redirect = self.redirect.get(request)

        with self.app.model.lock:
            issue_id = len(self.app.model.issues_by_id) + 1

            issue = Issue(self.app.model, issue_id)
            issue.summary = summary
            issue.description = description
            issue.keywords = keywords
        
        #return "/issue.html?id={}".format(issue.id)
        return redirect

class ReadIssue(Procedure):
    def __init__(self, app, name):
        super().__init__(app, name)

        self.id = IntegerParameter(self, "id")

    def render(self, request):
        issue_id = self.id.get(request)
        issue = self.app.model.issues_by_id[issue_id]

        data = {
            "id": issue.id,
            "summary": issue.summary,
            "description": issue.description,
            "keywords": issue.keywords,
        }
        
        return _json.dumps(data)

class ListIssues(Procedure):
    def render(self, request):
        issues = self.app.model.issues_by_id
        data = list()

        for id in sorted(issues):
            issue = issues[id]
            row = {
                "id": issue.id,
                "summary": issue.summary,
                "description": issue.description,
                "keywords": issue.keywords,
            }

            data.append(row)
        
        return _json.dumps(data)
    
home_dir = os.environ.get("TURRET_HOME", "/usr/share/turret")
files_dir = "output"

app = Demo(home_dir, files_dir)
proc = CreateIssue(app, "create-issue")
proc = ReadIssue(app, "read-issue")
proc = ListIssues(app, "list-issues")

with app.model.lock:
    issue = Issue(app.model, 1)
    issue.summary = """AMQP 1.0 jms client hangs when another reconnect should happen on the
        same MRGM broker"""
    issue.description = \
        """I mean, officially I deplore violence, but that was totally worth
        the loss of karma points! Hey, no, we'll just set course for
        Planet of the Lonely, Rich, and Appropriately Hygienic
        Man. You'll fight, and you'll shag, and you'll hate each other
        'til it makes you quiver, but you'll never be friends. These
        endless days are finally ending in a blaze. Time is what turns
        kittens into cats. Say! look at you! You look just like me!
        We're very pretty. Men watch the action movie, they eat of the
        beef, and enjoy to look at the bosoms. Or even worse, a
        sneezure. They rampaged through half the known world until
        Angel got his soul. Stay away from hyena people, or any loser
        athletes, or if you see anyone who's invisible.  If you can't
        do something smart, do something right. Better to cut you down
        to size, grandma. It eats you, starting with your
        bottom. Military people don't make out with science people. A
        vampire in love with a Slayer. It's rather poetic, in a
        maudlin sort of way. Can I start getting sexed already? You'll
        prove I can trust you when the day comes that you have to kill
        me. And you do. Can everybody just notice how much fire I'm
        not on? Shh! No programs, don't use that word. Just be
        Buffy. I like to think of myself more as a 'guest-age'.  In
        their resting state, our actives are as innocent and
        vulnerable as children. And I'm a huge fan of the way you lose
        control and turn into an enormous green rage monster. Freedom
        is life's great lie."""
    issue.keywords = "Whedon, Garbage, Deadlock"

    issue = Issue(app.model, 2)
    issue.summary = """update AMQP 1.0 selector filter handling to accept JMS Header names
        and align with client JMSType behaviour"""
    issue.description = \
        """The broker currently accepts (but does not advertise support for)
        selector filter values using the
        "apache.org:selector-filter:string" filter. This filter
        describes a mapping for JMS Header names in to an AMQP
        equivalent, so that non-JMS clients do not need to refer to
        the JMS header names. The old JMS client, and many if not all
        the other brokers using this filter do not perform this
        mapping, and send/recieve the JMS header names unchanged, and
        the new JMS client does the same for compatibility. As a
        result, certain operations do not work, such as attempting to
        select based on JMSCorrelationID.

        There are other issues with the filter as defined that are
        likely lead to a new one being defined for the long term, so
        after discussion it seems the easiest and cleanest way to
        resolve the current client interop issue with qpidd would be
        for the broker to accept the JMS header names in addition to
        the mapped AMQP equivalents.

        As part of this the handling for JMSType should be updated to
        actually align with what clients do. The filter defined that
        the value would be sent as the message annotation 'jms_type',
        but neither the old client or the new client do this, probably
        in part because the AMQP spec states that annotations not
        beginning "x-" are reserved and those not beginning "x-opt-"
        that are not understood MUST be met with link closure. The new
        JMS client sends the JMSType header value in the 'subject'
        field of the message Properties section. The old client sends
        it using the "x-opt-jms-type" symbol message annotation."""
    issue.keywords = "Patch, JMS, Interop"

setup_console_logging("debug")

app.init()
app.start()

def application(env, start_response):
    return app.application(env, start_response)
