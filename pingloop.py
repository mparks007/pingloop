import re
from enum import Enum

# ----------------------------------------------------------------------

# [FORMAT 1 - all good]
# Fri 07/14/2023 13:56:18.22

# Pinging www.google.com [142.250.115.106] with 32 bytes of data:
# Reply from 142.250.115.106: bytes=32 time=12ms TTL=105
# Reply from 142.250.115.106: bytes=32 time=11ms TTL=105
# Reply from 142.250.115.106: bytes=32 time=10ms TTL=105
# Reply from 142.250.115.106: bytes=32 time=10ms TTL=105

# Ping statistics for 142.250.115.106:
#     Packets: Sent = 4, Received = 3, Lost = 1 (25% loss),
# Approximate round trip times in milli-seconds:
#     Minimum = 10ms, Maximum = 13ms, Average = 11ms

# ----------------------------------------------------------------------

# [FORMAT 2 - mixed]
# Fri 07/14/2023 13:56:06.16

# Pinging www.google.com [142.250.115.106] with 32 bytes of data:
# Reply from 142.250.115.106: bytes=32 time=10ms TTL=105
# Reply from 142.250.115.106: bytes=32 time=13ms TTL=105
# Reply from 142.250.115.106: bytes=32 time=10ms TTL=105
# Request timed out.

# Ping statistics for 142.250.115.106:
#     Packets: Sent = 4, Received = 3, Lost = 1 (25% loss),
# Approximate round trip times in milli-seconds:
#     Minimum = 10ms, Maximum = 13ms, Average = 11ms

# ----------------------------------------------------------------------

# [FORMAT 3 - all bad]
# Fri 07/14/2023 13:56:18.22

# Pinging www.google.com [142.250.115.106] with 32 bytes of data:
# Request timed out.
# Request timed out.
# Request timed out.
# Request timed out.

# Ping statistics for 142.250.115.106:
#     Packets: Sent = 4, Received = 0, Lost = 4 (100% loss),

# ----------------------------------------------------------------------

# [FORMAT 4 - way bad]
# Fri 07/14/2023 13:56:18.22
# Ping request could not find host www.google.com. Please check the name and try again.

# set Enum to type str but forget why (I think I had in a print statement at some point)


class PingHealth(str, Enum):
    UNKNOWN = 0
    ALLGOOD = 1
    PARTIALGOOD = 2
    ALLBAD = 3
    VERYBAD = 4

# to store the four ping replies from a ping request


class PingSubResult:
    def __init__(self, response, succeeded):
        self.response = response
        self.succeeded = succeeded

    response = ''
    succeeded = False

# main ping attempt and result(s)


class PingResult:
    def __init__(self, timeStamp, pingSubResults=None):
        self.timeStamp = timeStamp
        # I think this is how to reset a list (otherwise it was remember last time's object)
        if pingSubResults is None:
            self.pingSubResults = []

    timeStamp = ''
    pingRequest = ''
    pingSubResults = []
    pingHealth = PingHealth.UNKNOWN


def LoadPingResults(filename):

    timeStampPattern = '^(?P<timeStamp>[A-Za-z]{3} \d{2}/\d{2}/\d{4}\s{1,2}\d{1,2}:\d{2}:\d{2}\.\d{2})'
    goodRequestPattern = '^(?P<goodRequest>Pinging)'
    badRequestPattern = '^(?P<badRequest>Ping request could not find host)'
    goodResponsePattern = '^(?P<goodResponse>Reply from)'

    pingResults = []
    inNewResultBlock = False

    # open up the ping results file for READ the start reading all lines
    with open(filename, "r", encoding="utf-8") as pingResultsFile:
        while True:
            pingResultsLine = pingResultsFile.readline()

            # if end of file
            if len(pingResultsLine) == 0:
                break

            # don't waste time on blank lines
            if len(pingResultsLine.rstrip('\n').strip()) < 1:
                continue

            # only try to match a time stamp if not already digging within a timestamp block
            if not inNewResultBlock:

                # try to find date/time (start of next ping attempt)
                timeStampMatch = re.match(timeStampPattern, pingResultsLine)
                if timeStampMatch:
                    inNewResultBlock = True
                    pingResult = PingResult(timeStampMatch.group('timeStamp'))
                    pingResults.append(pingResult)
                    continue

            # if had found a new timestamp, now dig into what happened at that time
            if inNewResultBlock:

                # try to find good request's respone
                goodRequestMatch = re.match(
                    goodRequestPattern, pingResultsLine)
                if goodRequestMatch:
                    pingResult.pingRequest = pingResultsLine

                    # initially, assume all good, but these will get overridden if find bad
                    pingResult.pingHealth = PingHealth.ALLGOOD
                    badPingCount = 0

                    # read the four, standard ping results
                    for i in range(4):
                        pingResultsLine = pingResultsFile.readline().rstrip('\n')

                        # capture the two types of ping responses, result or timed out (though I have no clue if there can be other types of responses)
                        goodResponseMatch = re.match(
                            goodResponsePattern, pingResultsLine)
                        if goodResponseMatch:
                            pingResult.pingSubResults.append(
                                PingSubResult(pingResultsLine, True))
                        else:
                            pingResult.pingSubResults.append(
                                PingSubResult(pingResultsLine, False))
                            badPingCount += 1

                    # override defaulted good
                    if badPingCount == 4:
                        pingResult.pingHealth = PingHealth.ALLBAD
                    elif badPingCount > 0:
                        pingResult.pingHealth = PingHealth.PARTIALGOOD

                else:
                    badRequestMatch = re.match(
                        badRequestPattern, pingResultsLine)
                    if badRequestMatch:
                        pingResult.pingRequest = pingResultsLine
                        pingResult.pingHealth = PingHealth.VERYBAD

                # should be done with the timestamps details so allow subsequent file reads to try and match on another timestamp
                inNewResultBlock = False

    return pingResults

# all individual fails per ping attempt
# ALLBAD|07/13/2023 20:24:30.15
# PARTIALGOOD|07/13/2023 20:24:53.21
# PARTIALGOOD|07/13/2023 20:42:56.19
# PARTIALGOOD|07/13/2023 20:45:07.20
# PARTIALGOOD|07/13/2023 21:00:46.12
# PARTIALGOOD|07/14/2023 10:42:49.14
# PARTIALGOOD|07/14/2023 11:59:56.12
# PARTIALGOOD|07/14/2023 12:39:27.21
# VERYBAD|07/14/2023 13:18:19.14
# VERYBAD|07/14/2023 13:18:35.22

# durations summary


def SummarizePingFailures(pingResults):

    allGood = []
    partialGood = []
    allBad = []
    veryBad = []

    # open up the output file for CREATE/APPEND
    with open(".\output\pingResults.txt", "a+", encoding="utf-8") as outputFile:

        for i in range(len(pingResults)):
            pingResult = pingResults[i]

            # build out results lists, by severity
            if pingResult.pingHealth == PingHealth.ALLGOOD:
                allGood.append(pingResult.timeStamp)
            elif pingResult.pingHealth == PingHealth.PARTIALGOOD:
                partialGood.append(pingResult.timeStamp)
            elif pingResult.pingHealth == PingHealth.ALLBAD:
                allBad.append(pingResult.timeStamp)
            elif pingResult.pingHealth == PingHealth.VERYBAD:
                veryBad.append(pingResult.timeStamp)

            # write out a format easy to parse in excel
            outputLine = pingResult.pingHealth.name + \
                "|" + pingResult.timeStamp[4:] + "\n"
            outputFile.write(outputLine)

    print("Pings with all good results: " + str(len(allGood)))
    # print(allGood)

    print("Pings with mixed failures: " + str(len(partialGood)))
    # print(partialGood)

    print("Pings with all four failures: " + str(len(allBad)))
    # print(allBad)

    print("Pings that couldn't even try: " + str(len(veryBad)))
    # print(veryBad)


if __name__ == "__main__":

    # snag all the data from the ping loop capture
    pingResults = LoadPingResults('.\input\pingloop1.txt')

    # print out all results cases/counts
    SummarizePingFailures(pingResults)

    print('Done')
