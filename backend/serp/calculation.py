from django.shortcuts import render
from django.conf import settings

from serp.models import Keyword, Language, Region, Header, Groups, Feedback, Refreshmanual, Subscriptionplans, Accountusage, Settings

import requests, json, time
import sys, os, random
from datetime import datetime, date, timedelta
from collections import defaultdict

from django.db.models import Q

from shared.scoring import calculate_visibility_score_from_buckets


def activityCalc(improve, declined, allKey):
    if allKey > 0:
        # return round(float( ((len(improve) - len(declined)) / allKey) * 100 ), 2)
        activityResult = round(float(((len(improve) - len(declined)) / allKey) * 100), 2)
        return str(activityResult) + "|" + str(len(improve)) + "|" + str(len(declined))
    else:
        return "0|0|0"


def scoreAllocationCalc(keyIns, scorePerDay, totalRankLength=int(100)):
    rank_array = list()
    if hasattr(keyIns, "rank"):
        rank_array = keyIns.rank
    elif "rank" in keyIns:
        rank_array = keyIns["rank"]
    elif isinstance(keyIns, dict):
        rank_array = keyIns["RK"] if "RK" in keyIns else list()

    if len(rank_array) > 0:
        if rank_array[0] == 1:
            scorePerDay["eq__first"] += 1
        elif rank_array[0] == 2:
            scorePerDay["eq__second"] += 1
        elif rank_array[0] == 3:
            scorePerDay["eq__third"] += 1
        elif rank_array[0] <= 10 and rank_array[0] > 3:
            scorePerDay["gte__four__lte__ten"] += 1
        elif rank_array[0] > 10 and rank_array[0] <= totalRankLength:
            scorePerDay["gt__ten__lte__limit"] += 1
        else:
            scorePerDay["gt__limit"] += 1
    else:
        scorePerDay["gt__limit"] += 1

    return scorePerDay


def scoreMeterCalc(scorePerDay, allKey):
    """Visibility score from the rank bucket counts. One formula, one place.

    This used to carry its own copy of the weight ladder, and the copy had
    drifted: it weighted `gt__limit` (unranked) at **-0.10** where
    shared.scoring weights it 0.0. The same project therefore scored 34 here
    -- /keywords and the stored Groups.score_meter -- and 37 through
    /erocs_wdt, which goes via shared.scoring. The gap was exactly the
    unranked penalty, so it widened with every keyword that had not ranked
    yet, i.e. it was worst on a new project.

    Delegating matches what engine/project/machine/formulate.py already does
    (and what tests/test_product_surface.py asserts of it). Penalising an
    unranked keyword below zero also double-counted it: it is already in the
    denominator, so it already drags the average down.
    """
    return calculate_visibility_score_from_buckets(scorePerDay, allKey)


def rankFormulation(liveRank, pastRank):
    totalRankLength = int(100)

    if int(liveRank) == 0 and int(pastRank) == 0:
        formulateValue = 0
    elif int(liveRank) == 0 and int(pastRank) > 0:
        formulateValue = int(pastRank) - int(totalRankLength)
    elif int(liveRank) > 0 and int(pastRank) == 0:
        formulateValue = int(totalRankLength) - int(liveRank)
    elif int(liveRank) > int(pastRank):
        formulateValue = int(pastRank) - int(liveRank)
    elif int(pastRank) > int(liveRank):
        formulateValue = int(pastRank) - int(liveRank)
    else:
        formulateValue = int(liveRank) - int(pastRank)

    return formulateValue


def timeDifference(startTime, endTime, timeIn):
    diff = endTime - startTime
    if timeIn == "days":
        return diff.days
    elif timeIn == "hours":
        return diff.seconds / 3600
    elif timeIn == "minutes":
        return diff.seconds / 60
    elif timeIn == "seconds":
        return diff.seconds
    elif timeIn == "microseconds":
        return diff.microseconds
    else:
        return 0


def sinceStartCalc(userid, grpid):
    topset = ["0-1", "1-2", "2-3", "3-10", "10-100", "0-0"]
    singleSinceStart = []
    singleSincePosition = []

    for tset in topset:
        positiveCount = 0
        negativeCount = 0

        topRankVal = tset.split("-")

        if len(topRankVal) > 1:
            minVal = int(topRankVal[0])
            maxVal = int(topRankVal[1])

            if minVal == 0 and maxVal == 0:
                headerKeywordCount = Keyword.objects.filter((Q(ranknow=0)) & Q(fk_user_id=userid) & Q(fk_group_id=grpid)).count()
                positiveCount = 0
                negativeCount = 0
            else:
                positiveFilter = Keyword.objects.filter(Q(fk_user_id=userid) & Q(fk_group_id=grpid) & (Q(rank_sincestart=0) | Q(rank_sincestart__gt=maxVal)) & (Q(ranknow__gt=minVal) & Q(ranknow__lte=maxVal)))

                negativeFilter = Keyword.objects.filter(Q(fk_user_id=userid) & Q(fk_group_id=grpid) & (Q(rank_sincestart__gt=minVal) & Q(rank_sincestart__lte=maxVal)) & (Q(ranknow=0) | Q(ranknow__gt=maxVal)))

                headerKeywordCount = Keyword.objects.filter((Q(ranknow__gt=minVal) & Q(ranknow__lte=maxVal)) & Q(fk_user_id=userid) & Q(fk_group_id=grpid)).count()

                positiveCount = positiveFilter.count()
                negativeCount = negativeFilter.count()

            markValue = positiveCount - negativeCount

            # CHANGE | POSITIVE | NEGATIVE
            singleSinceStart.append(str(markValue) + "|" + str(positiveCount) + "|" + str(negativeCount))
            singleSincePosition.append(str(headerKeywordCount))
        else:
            # CHANGE | POSITIVE | NEGATIVE
            singleSinceStart.append("0|0|0")
            singleSincePosition.append("0")

    return ",".join(map(str, singleSinceStart)) + "~~" + ",".join(map(str, singleSincePosition))


def OnUpdateToGroup(userid, grpid):
    startTime = datetime.now()
    totalRankLength = int(100)
    currdate = date.today()

    if userid and grpid:
        GroupData = Groups.objects.filter(fk_user_id=userid, id=grpid)
        if GroupData.count() > 0:
            for GroupIns in GroupData:
                if GroupIns.id:
                    singleGroupUpdate = Groups.objects.get(id=GroupIns.id)
                    singleGroup = singleGroupUpdate
                    groupAge = int((currdate - singleGroup.created_date.date()).days) + 1
                    userid = GroupIns.fk_user_id
                    rankIndexCount = int(groupAge)
                    if len(singleGroup.total_Keyword) > groupAge:
                        groupDifference = len(singleGroup.total_Keyword) - groupAge
                        flag = 1
                        while flag <= groupDifference:
                            singleGroupUpdate.score_meter.pop(0)
                            singleGroupUpdate.activity_level.pop(0)
                            singleGroupUpdate.since_start.pop(0)
                            singleGroupUpdate.since_position.pop(0)
                            singleGroupUpdate.total_Keyword.pop(0)
                            singleGroupUpdate.updated_date = datetime.now()
                            singleGroupUpdate.save()
                            flag += 1

                    if (groupAge == (len(singleGroup.total_Keyword) + 1) and len(singleGroup.total_Keyword) > 0) or (groupAge == len(singleGroup.total_Keyword) and len(singleGroup.total_Keyword) > 0):
                        if groupAge == len(singleGroup.total_Keyword):
                            singleGroupUpdate.score_meter.pop(0)
                            singleGroupUpdate.activity_level.pop(0)
                            singleGroupUpdate.since_start.pop(0)
                            singleGroupUpdate.since_position.pop(0)
                            singleGroupUpdate.total_Keyword.pop(0)
                            singleGroupUpdate.updated_date = datetime.now()
                            singleGroupUpdate.save()

                        single_date = currdate + timedelta(1)
                        allKeywords = Keyword.objects.filter(fk_group_id=GroupIns.id, created_date__lt=single_date).all()
                        scorePerDay = defaultdict(int)
                        improvedKeywords = []
                        declinedKeywords = []

                        for keyIns in allKeywords:
                            scorePerDay = scoreAllocationCalc(keyIns, scorePerDay, totalRankLength)

                            if rankIndexCount >= len(keyIns.rank) and len(keyIns.rank) > 1:
                                dayDiff = rankFormulation(keyIns.rank[0], keyIns.rank[1])
                                if dayDiff > 0:
                                    improvedKeywords.insert(0, str(dayDiff) + " & " + str(keyIns.id))
                                elif dayDiff < 0:
                                    declinedKeywords.insert(0, str(dayDiff) + " & " + str(keyIns.id))

                        sinceStartExplode = sinceStartCalc(userid, GroupIns.id).split("~~")

                        singleGroupUpdates = Groups.objects.get(id=GroupIns.id)
                        singleGroupUpdates.score_meter.insert(0, str(scoreMeterCalc(scorePerDay, len(allKeywords))))
                        singleGroupUpdates.activity_level.insert(0, str(activityCalc(improvedKeywords, declinedKeywords, len(allKeywords))))
                        singleGroupUpdates.total_Keyword.insert(0, str(len(allKeywords)))
                        singleGroupUpdates.since_start.insert(0, str(str(sinceStartExplode[0])))
                        singleGroupUpdates.since_position.insert(0, str(str(sinceStartExplode[1])))
                        singleGroupUpdates.updated_date = datetime.now()
                        singleGroupUpdates.save()
                        return True
                    else:
                        return False
        else:
            return False
    else:
        return False


def sampleCheck(userid, grpid):
    return True
