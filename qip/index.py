import os
import sys

def get_title(content_path):
    lines = open(content_path).readlines()
    title = None

    for line in lines:
        if line.startswith("# "):
            title = line[2:-1]
            break

    return title

def get_qip_links(dir_path):
    links = dict()

    for name in os.listdir(dir_path):
        if not name.endswith(".md"):
            continue

        path = os.path.join(dir_path, name)
        title = get_title(path)
        head, tail = os.path.splitext(name)

        links[title] = "draft/%s.html" % head

    lines = list()

    for args in sorted(links.items()):
        lines.append(" * [%s](%s)" % args)

    return "\n".join(lines)

def main(template_path):
    path = os.path.join("draft")
    qips = get_qip_links(path)

    template = open(template_path).read()
    template = template.replace("@draft_qips@", qips)

    sys.stdout.write(template)

if __name__ == "__main__":
    main(*sys.argv[1:])
