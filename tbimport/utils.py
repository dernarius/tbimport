from typing import NamedTuple
import csv
import yaml
from urllib.parse import urljoin

import requests
import pandas as pd


class Adjudicator(NamedTuple):
    name: str
    email: str
    school: str
    base_score: float


class Debater(NamedTuple):
    name: str
    email: str


class Team(NamedTuple):
    name: str
    school: str
    members: list[Debater]


class Settings(NamedTuple):
    host: str
    api_key: str
    slug: str
    break_category_id: int


class ApiSession(requests.Session):
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        joined_url = urljoin(self.base_url, f"/api/v1{url}")
        return super().request(method, joined_url, *args, **kwargs)


def get_config():
    with open("settings.yaml") as f:
        di = yaml.load(f, Loader=yaml.Loader)

    settings = Settings(
        host=di.get("host"),
        api_key=di.get("apikey"),
        slug=di.get("slug"),
        break_category_id=di.get("break_category_id"),
    )

    return settings


def create_session():
    settings = get_config()
    s = ApiSession(base_url=settings.host)
    s.headers["Authorization"] = f"Token {settings.api_key}"
    return s


def read_teams(filename) -> list[Team]:
    df = pd.read_csv("teams.csv")
    melted = df.melt(
        id_vars=("school", "team_name"),
    )
    melted[melted["value"] == "-"] = pd.NA
    melted = melted.dropna()
    melted[["variable", "num"]] = melted["variable"].str.split("_", expand=True)[[0, 1]]

    unmelted = melted.pivot(
        columns="variable", index=("school", "team_name", "num")
    ).reset_index()

    grouped = unmelted.groupby(["school", "team_name"])

    teams = grouped.apply(
        lambda x: Team(
            name=x.name[1],
            school=x.name[0].strip(),
            members=x.apply(
                lambda x: Debater(name=x["value"]["name"], email=x["value"]["email"]),
                axis=1,
            ).tolist(),
        )
    ).tolist()

    return teams


def read_judges(filename) -> list[Adjudicator]:
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        judges = [
            Adjudicator(
                name=x.get("name").strip(),
                school=x.get("school").strip(),
                email=x.get("email").strip(),
                base_score=float(x.get("score", "0.0").strip()),
            )
            for x in reader
        ]
        return judges


def build_insts_dict(s: ApiSession):
    req = s.get("/institutions")
    req.raise_for_status()
    return {
        **{x.get("code"): (x.get("url"), x.get("code")) for x in req.json()},
        **{x.get("name"): (x.get("url"), x.get("code")) for x in req.json()},
    }
