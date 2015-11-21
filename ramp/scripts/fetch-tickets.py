#!/usr/bin/python

import sys
import urllib

def main():
    query = sys.argv[1]
    output = sys.argv[2]

    params = dict()
    params['jqlQuery'] = query

    url = "https://issues.apache.org/jira/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?%s" % urllib.urlencode(params)

    urllib.urlretrieve(url, output)

if __name__ == "__main__":
    main()
