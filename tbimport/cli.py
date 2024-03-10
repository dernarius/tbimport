import click

import tbimport.utils as u


@click.group()
def cli():
    pass


@cli.command()
def ensure_institutions():
    s = u.create_session()

    api_institutions = {di.get("name") for di in s.get("/institutions").json()}
    team_institutions = {t.school for t in u.read_teams("teams.csv")}
    adj_institutions = {a.school for a in u.read_judges("judges.csv")}

    to_create = (team_institutions | adj_institutions) - api_institutions
    to_create -= {"", "-", "–"}

    click.echo(f"Creating {len(to_create)} institutions: {to_create}")

    for inst in to_create:
        abbr = "".join(x for x in inst if x.isupper())
        try:
            body = {
                "name": inst,
                "code": abbr,
            }
            req = s.post(
                "/institutions",
                json=body,
            )
            req.raise_for_status()
        except:
            print(body)


@cli.command()
def import_judges():
    config = u.get_config()
    s = u.create_session()

    insts = u.build_insts_dict(s)

    click.echo("read insts dict")

    judges = u.read_judges("judges.csv")
    click.echo("read insts judges")

    for i, j in enumerate(judges):
        click.echo(f"importing judge {i}: {j}")
        school = insts.get(j.school)

        body = {
            "name": j.name,
            "email": j.email,
            "institution": school[0] if school else None,
            "institution_conflicts": [school[0]] if school else [],
            "team_conflicts": [],
            "adjudicator_conflicts": [],
            "base_score": 0.0,
        }

        req = s.post(
            f"/tournaments/{config.slug}/adjudicators",
            json=body,
        )
        if req.status_code >= 300:
            print(req.json())
            req.raise_for_status()


@cli.command()
def import_teams():
    config = u.get_config()
    s = u.create_session()

    insts = u.build_insts_dict(s)
    teams = u.read_teams("teams.csv")

    for t in teams:
        school = insts.get(t.school)
        req = s.post(
            f"/tournaments/{config.slug}/teams",
            json={
                "reference": t.name,
                "short_reference": t.name[:35],
                "institution": school[0],
                "speakers": [
                    {"name": speaker.name, "email": speaker.email, "categories": []}
                    for speaker in t.members
                    if speaker.name
                ],
                "use_institution_prefix": False,
                "break_categories": [
                    f"https://tab.pikta.lt/api/v1/tournaments/{config.slug}"
                    f"/break-categories/{config.break_category_id}"
                ],
                "institution_conflicts": [school[0]],
            },
        )
        if req.status_code >= 300:
            print(t)
            print(req.json())
            req.raise_for_status()
        else:
            print(t)


@cli.command()
def set_human_category():
    s = u.create_session()

    speakers_req = s.get("/tournaments/lsdl0/speakers")
    speakers_req.raise_for_status()

    for speaker in speakers_req.json():
        if "Speaker" not in speaker["name"]:
            speaker["categories"] = [
                "https://tab.pikta.lt/api/v1/tournaments/lsdl0/speaker-categories/1"
            ]
            speaker_id = speaker.pop("id")
            update_req = s.patch(
                f"/tournaments/lsdl0/speakers/{speaker_id}", json=speaker
            )
            update_req.raise_for_status()
