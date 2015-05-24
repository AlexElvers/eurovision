#!/usr/bin/env python3

"""
Author: Alexander Elvers (@AlexElvers)
License of the code: CC-BY 4.0

CSV data:
Source: English Wikipedia, articles of the corresponding years
License: CC-BY-SA 3.0
"""

import csv
import pathlib
import collections

class Eurovision:
    def __init__(self, min_vote=0, folder="data", debug=False):
        self.voters = set()
        self.min_vote = min_vote
        self.folder = pathlib.Path(folder)
        self.debug = debug
        self.votes = {} # {year: {voter: {contestant: score}}}

    def read_all(self, years=None):
        """
        Read all files from the data folder. If years are given, read only
        these.
        """
        if years:
            filenames = [self.folder / ("%d.csv" % year) for year in years]
        else:
            filenames = sorted(self.folder.glob("*.csv"))
        for filename in filenames:
            self.votes[filename.stem] = self.read_file(str(filename))

    def read_file(self, filename):
        """
        Fill eurovision.votes with data from the file.
        """
        votes = {}

        with open(filename) as f:
            reader = csv.DictReader(f, dialect="excel-tab")

            line_counter = 0
            for contestant_row in reader:
                if contestant_row:
                    line_counter += 1
                    for voter in contestant_row:
                        assert voter is not None, "voter is None for contestant %s" % contestant_row.get("Contestant", "-unknown contestant-")
                        if voter.lower() == "contestant" or voter.lower() == "total score":
                            continue
                        if not contestant_row[voter] or contestant_row[voter] == "-":
                            score = 0
                        else:
                            score = int(contestant_row[voter])
                        if score >= self.min_vote:
                            votes.setdefault(voter, {})[contestant_row["Contestant"]] = score
                else:
                    break

            fieldnames = set(reader.fieldnames)
            for fieldname in fieldnames.copy():
                if fieldname.lower() == "contestant" or fieldname.lower() == "total score":
                    fieldnames.remove(fieldname)
            self.voters.update(fieldnames)

            if self.debug:
                print("file", filename, line_counter, "participants", len(fieldnames), "voters")

            return votes

    def voter_sum(self, voter):
        """
        Calculate the sum for a voting country on the whole data.
        """
        scores = collections.Counter()
        count = 0

        for year in self.votes:
            if voter in self.votes[year]:
                count += 1
                scores.update(self.votes[year][voter])

        return scores, count

    def print_most_common(self, limit=5):
        """
        Print the most common votes.

        For an HTML file, use generate_html().
        """
        for voter in sorted(self.voters):
            print(voter, end=":\t")

            scores, count = self.voter_sum(voter)
            for contestant, score in scores.most_common(limit):
                if score > 0:
                    print("%.1f" % (score / count), contestant, end="\t")

            print("(%d votings)" % count)

    def generate_html(self, limit=None, minimum=0, chart_width=None, chart_height=None):
        """
        Generate an HTML file which contains a diagram showing the voting
        behaviour.  For each voting country, only connections with a
        minimum average show up, limited to the 'limit' highest points.
        """
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("base.html")

        rows = []
        for voter in sorted(self.voters):
            scores, count = self.voter_sum(voter)
            for contestant, score in scores.most_common(limit):
                if score > minimum * count:
                    rows.append({
                        "from": voter,
                        "to": contestant,
                        "weight": score / count,
                        "score": score,
                        "voting_count": count,
                    })

        with open("eurovision.html", "w") as f:
            print(template.render(
                rows=rows,
                limit=limit,
                minimum_average=minimum,
                minimum_vote=self.min_vote,
                chart_width=chart_width,
                chart_height=chart_height,
            ), file=f)


if __name__ == "__main__":
    eurovision = Eurovision()
    eurovision.read_all()
    # eurovision.print_most_common()
    eurovision.generate_html(minimum=6)
