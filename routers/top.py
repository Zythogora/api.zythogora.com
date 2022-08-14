from argon2 import PasswordHasher
from config import connection, search
from fastapi import APIRouter, HTTPException
import jwt
import os
from pydantic import BaseModel
import time
import re

import routers.beers as r_beers
import routers.breweries as r_breweries

router = APIRouter()



@router.get("/top/beers", tags=["top"])
async def get_top_beers(count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT
                Ratings.beer,
                (SUM(Ratings.score) + BayesianConstants.m * BayesianConstants.C) / (COUNT(Ratings.id) + BayesianConstants.C) AS bayesian_score,
                AVG(Ratings.date) AS average_date
            FROM
                Ratings,
                (
                    SELECT
                        AVG(UserRatings.score) as m,
                        AVG(SortedUserRatings.score) as C
                    FROM
                        (
                            SELECT
                                Ratings.score
                            FROM
                                Ratings
                        ) AS UserRatings,
                        (
                            SELECT
                                SubSortedUserRatings.*,
                                Percentile.value AS rank_max
                            FROM
                                (
                                    SELECT
                                        Ratings.*,
                                        @rownum := @rownum + 1 AS rank
                                    FROM
                                        Ratings,
                                        (
                                            SELECT
                                                @rownum := 0
                                        ) r
                                    ORDER BY
                                        Ratings.score ASC
                                ) AS SubSortedUserRatings,
                                (
                                    SELECT
                                        FLOOR(0.25 * COUNT(Ratings.id)) AS value
                                    FROM
                                        Ratings
                                ) Percentile
                        ) AS SortedUserRatings
                    WHERE
                        SortedUserRatings.rank < SortedUserRatings.rank_max
                ) AS BayesianConstants
            GROUP BY
                Ratings.beer
            ORDER BY
                bayesian_score DESC,
                average_date DESC
            LIMIT %s, %s
        """, ((page - 1) * count, count))
        query_beers = cursor.fetchall()

        res = [ ]
        for row in query_beers:
            beer = await r_beers.get_beer(row[0])
            res.append(beer)

        return res



@router.get("/top/beers/{user}", tags=["top"])
async def get_user_top_beers(user: str, count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid=%s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username=%s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT
                Ratings.beer,
                (SUM(Ratings.score) + BayesianConstants.m * BayesianConstants.C) / (COUNT(Ratings.id) + BayesianConstants.C) AS bayesian_score,
                AVG(Ratings.date) AS average_date
            FROM
                Ratings,
                (
                    SELECT
                        AVG(UserRatings.score) as m,
                        AVG(SortedUserRatings.score) as C
                    FROM
                        (
                            SELECT
                                Ratings.score
                            FROM
                                Ratings
                            WHERE
                                Ratings.user = %s
                        ) AS UserRatings,
                        (
                            SELECT
                                SubSortedUserRatings.*,
                                Percentile.value AS rank_max
                            FROM
                                (
                                    SELECT
                                        Ratings.*,
                                        @rownum := @rownum + 1 AS rank
                                    FROM
                                        Ratings,
                                        (
                                            SELECT
                                                @rownum := 0
                                        ) r
                                    WHERE
                                        Ratings.user = %s
                                    ORDER BY
                                        Ratings.score ASC
                                ) AS SubSortedUserRatings,
                                (
                                    SELECT
                                        FLOOR(0.25 * COUNT(Ratings.id)) AS value
                                    FROM
                                        Ratings
                                    WHERE
                                        Ratings.user = %s
                                ) Percentile
                        ) AS SortedUserRatings
                    WHERE
                        SortedUserRatings.rank < SortedUserRatings.rank_max
                ) AS BayesianConstants
            WHERE
                Ratings.user = %s
            GROUP BY
                Ratings.beer
            ORDER BY
                bayesian_score DESC,
                average_date DESC
            LIMIT %s, %s
        """, (query_users[0], query_users[0], query_users[0], query_users[0], (page - 1) * count, count))
        query_beers = cursor.fetchall()

        res = [ ]
        for row in query_beers:
            beer = await r_beers.get_beer(row[0])
            res.append(beer)

        return res



@router.get("/top/breweries", tags=["top"])
async def get_top_breweries(count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT
                Beers.brewery,
                AVG(bayesian_score),
                AVG(average_date)
            FROM
                (
                    SELECT
                        Ratings.beer,
                        (SUM(Ratings.score) + BayesianConstants.m * BayesianConstants.C) / (COUNT(Ratings.id) + BayesianConstants.C) AS bayesian_score,
                        AVG(Ratings.date) AS average_date
                    FROM
                        Ratings,
                        (
                            SELECT
                                AVG(UserRatings.score) as m,
                                AVG(SortedUserRatings.score) as C
                            FROM
                                (
                                    SELECT
                                        Ratings.score
                                    FROM
                                        Ratings
                                ) AS UserRatings,
                                (
                                    SELECT
                                        SubSortedUserRatings.*,
                                        Percentile.value AS rank_max
                                    FROM
                                        (
                                            SELECT
                                                Ratings.*,
                                                @rownum := @rownum + 1 AS rank
                                            FROM
                                                Ratings,
                                                (
                                                    SELECT
                                                        @rownum := 0
                                                ) r
                                            ORDER BY
                                                Ratings.score ASC
                                        ) AS SubSortedUserRatings,
                                        (
                                            SELECT
                                                FLOOR(0.25 * COUNT(Ratings.id)) AS value
                                            FROM
                                                Ratings
                                        ) Percentile
                                ) AS SortedUserRatings
                            WHERE
                                SortedUserRatings.rank < SortedUserRatings.rank_max
                        ) AS BayesianConstants
                    GROUP BY
                        Ratings.beer
                ) AS SortedBeers
                LEFT JOIN Beers ON Beers.id = SortedBeers.beer
            GROUP BY
                Beers.brewery
            ORDER BY
                bayesian_score DESC,
                average_date DESC
            LIMIT %s, %s
        """, ((page - 1) * count, count))
        query_breweries = cursor.fetchall()

        res = [ ]
        for row in query_breweries:
            brewery = await r_breweries.get_brewery(row[0])
            res.append(brewery)

        return res



@router.get("/top/breweries/{user}", tags=["top"])
async def get_user_top_breweries(user: str, count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid=%s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username=%s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT
                Beers.brewery,
                AVG(bayesian_score),
                AVG(average_date)
            FROM
                (
                    SELECT
                        Ratings.beer,
                        (SUM(Ratings.score) + BayesianConstants.m * BayesianConstants.C) / (COUNT(Ratings.id) + BayesianConstants.C) AS bayesian_score,
                        AVG(Ratings.date) AS average_date
                    FROM
                        Ratings,
                        (
                            SELECT
                                AVG(UserRatings.score) as m,
                                AVG(SortedUserRatings.score) as C
                            FROM
                                (
                                    SELECT
                                        Ratings.score
                                    FROM
                                        Ratings
                                    WHERE
                                        Ratings.user = %s
                                ) AS UserRatings,
                                (
                                    SELECT
                                        SubSortedUserRatings.*,
                                        Percentile.value AS rank_max
                                    FROM
                                        (
                                            SELECT
                                                Ratings.*,
                                                @rownum := @rownum + 1 AS rank
                                            FROM
                                                Ratings,
                                                (
                                                    SELECT
                                                        @rownum := 0
                                                ) r
                                            WHERE
                                                Ratings.user = %s
                                            ORDER BY
                                                Ratings.score ASC
                                        ) AS SubSortedUserRatings,
                                        (
                                            SELECT
                                                FLOOR(0.25 * COUNT(Ratings.id)) AS value
                                            FROM
                                                Ratings
                                            WHERE
                                                Ratings.user = %s
                                        ) Percentile
                                ) AS SortedUserRatings
                            WHERE
                                SortedUserRatings.rank < SortedUserRatings.rank_max
                        ) AS BayesianConstants
                    WHERE
                        Ratings.user = %s
                    GROUP BY
                        Ratings.beer
                ) AS SortedBeers
                LEFT JOIN Beers ON Beers.id = SortedBeers.beer
            GROUP BY
                Beers.brewery
            ORDER BY
                bayesian_score DESC,
                average_date DESC
            LIMIT %s, %s
        """, (query_users[0], query_users[0], query_users[0], query_users[0], (page - 1) * count, count))
        query_breweries = cursor.fetchall()

        res = [ ]
        for row in query_breweries:
            brewery = await r_breweries.get_brewery(row[0])
            res.append(brewery)

        return res