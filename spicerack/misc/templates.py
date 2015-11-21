text0 = """
<form id="{id}" class="QueueForm mform" method="post" action="?">
  <div class="head">
    <h1>{title}</h1>
  </div>
  <div class="body">
    <span class="legend">Name</span>
    <fieldset>
      <div class="field">{queue_name}</div>
    </fieldset>
    <span class="legend">Latency Tuning</span>
    <fieldset>
      <div class="field">
        {latency}
        <em>Lower Latency:</em> Tune for shorter delays, with reduced volume
      </div>
      <div class="field">
        {balanced}
        <em>Balanced</em>
      </div>
      <div class="field">
        {throughput}
        <em>Higher Throughput:</em> Tune for increased volume, with longer
        delays
      </div>
    </fieldset>
    <span class="legend">Realms</span>
    <fieldset>{realms}</fieldset>
{hidden_inputs}
  </div>
  <div class="foot">
    <div style="display: block; float: left;"><button>Help</button></div>
{cancel}
{submit}
  </div>
</form>
<script defer="defer">
(function() {
    var elem = wooly.doc().elem("{id}").node.elements[1];
    elem.focus();
    elem.select();
}())
</script>
"""

def parse(text):
    fragments = list()

    start = 0
    end = text.find("{")

    while True:
        if (end == -1):
            fragments.append(text[start:])
            break

        fragments.append(text[start:end])

        ccurly = text.find("}", end + 1)

        if ccurly == -1:
            start = end
            end = -1
        else:
            ocurly = text.find("{", end + 1)

            if ocurly == -1:
                start = end
                end = ccurly + 1
            elif ocurly < ccurly:
                start = end
                end = ocurly
            else:
                fragments.append("{" + text[end + 1:ccurly] + "}")

                start = ccurly + 1
                end = ocurly

    return fragments

if __name__ == "__main__":
    from time import clock
    from cStringIO import StringIO

    texts = ["x{y}z}a{b}c",
             "x{y",
             "x}y",
             "{{{",
             "}{}{",
             "x{y{z}"]

    for text in texts:
        print text, parse(text)

    frags = None
    start = clock()

    for i in range(10000):
        frags = parse(text0)

    print clock() - start

    start = clock()

    for i in range(10000):
        buffer = StringIO()

        for frag in frags:
            buffer.write(frag)

    print clock() - start
