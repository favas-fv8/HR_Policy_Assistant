from django.db import migrations
import re

FALLBACK = {"", "new chat", "new conversation", "user question"}
FILLER = {
    "a","an","the","please","kindly","can","could","would","you","me","my","i","we","us","our","tell","about","for","to","of",
    "in","on","at","is","are","was","were","do","does","did","what","whats","what's","how","why","when","where","who","which",
    "should","will","may","might","need","want","like","give","show","explain","describe","summarize","summary","provide","get",
    "let","know","any","some","this","that","these","those","it"
}
GREET = {"hi","hello","hey","greetings","good","morning","afternoon","evening","thanks","thank"}

def _cap(w):
    u=w.upper()
    if u in {"HR","PDF","AI","IT","PTO","USA","UK"}: return u
    if any(c.isdigit() for c in w) or "/" in w or "&" in w or "-" in w:
        return w.upper() if w.isupper() else w[:1].upper()+w[1:]
    return w.capitalize()

def gen(msg):
    text=(msg or "").strip()
    if not text: return "New Chat"
    text=re.sub(r"https?://\S+|www\.\S+|\S+@\S+"," ",text)
    text=re.sub(r"[`*_#>\[\](){}]"," ",text)
    text=re.sub(r"\s+"," ",text).strip()
    if not text: return "New Chat"
    seg=next((s.strip() for s in re.split(r"[?!.:\n\r]+",text) if s.strip()), text)
    words=re.findall(r"[A-Za-z0-9][A-Za-z0-9&/-]*", seg)
    if not words: return "New Chat"
    i=0
    while i < len(words) and words[i].lower() in GREET: i+=1
    words=words[i:] or words
    filtered=[w for w in words if w.lower() not in FILLER]
    if not filtered: filtered=[w for w in words if w.lower() not in GREET]
    if not filtered: return "New Chat"
    tw=filtered[:7]
    while len(tw)>3 and tw[-1].lower() in {"and","or","for","to","of","with","by"}: tw.pop()
    title=" ".join(_cap(w) for w in tw).strip()
    title=re.sub(r"\s+"," ",title)
    if len(title)>60:
        title=title[:60].rstrip(" -,:;")
        if " " in title:
            p=title.rsplit(" ",1)
            if len(p[0])>=20: title=p[0]
    title=title.strip(" -,:;!?")
    return title or "New Chat"

def backfill(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    Message = apps.get_model('chat', 'Message')
    for conv in Conversation.objects.all().only('id','title'):
        if (conv.title or '').strip().lower() not in FALLBACK:
            continue
        first = Message.objects.filter(conversation_id=conv.id, role='user').order_by('created_at','id').first()
        if not first:
            continue
        new_title = gen(first.content)
        if new_title and new_title != conv.title:
            Conversation.objects.filter(id=conv.id, title=conv.title).update(title=new_title)

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(backfill, noop),
    ]
