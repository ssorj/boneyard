import markdown2
import sys

def main(content_path, template_path):
    content_lines = open(content_path).readlines()
    title = None

    for line in content_lines:
        if line.startswith("# "):
            title = line[2:]
            break

    assert title


    content = "".join(content_lines)

    md = markdown2.Markdown()
    content = md.convert(content)

    template = open(template_path).read()
    template = template.replace("@title@", title)
    template = template.replace("@content@", content)

    sys.stdout.write(template)

if __name__ == "__main__":
    main(*sys.argv[1:])
