import base64
import os
from googleapiclient.errors import HttpError

from gmail_app import create_gmail_service


def list_message_ids(service, query="has:attachment", max_results=50):
    """
    Return message IDs matching a Gmail search query.
    `query` uses Gmail search syntax, e.g.:
        "has:attachment"
        "has:attachment from:vendor@x.com newer_than:30d"
        "has:attachment filename:pdf"
    """
    ids = []
    page_token = None
    while True:
        resp = service.users().messages().list(
            userId="me",
            q=query,
            pageToken=page_token,
            maxResults=min(max_results - len(ids), 100),
        ).execute()

        ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")

        if not page_token or len(ids) >= max_results:
            break

    return ids[:max_results]


def get_message(service, message_id):
    """Fetch the full message (headers + MIME tree, but not attachment bytes)."""
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()


def _header(headers, name):
    """Pull a header value by name (case-insensitive)."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None


def walk_parts(payload):
    """
    Recursively yield every leaf part in the MIME tree.
    A container part (multipart/*) has `parts`; leaves don't.
    """
    if "parts" in payload:
        for part in payload["parts"]:
            yield from walk_parts(part)
    else:
        yield payload


def extract_attachment_metadata(message):
    """
    Return a list of attachment descriptors from a message.
    Each descriptor has enough to fetch the bytes later.
    """
    attachments = []
    payload = message.get("payload", {})

    for part in walk_parts(payload):
        filename = part.get("filename")
        body = part.get("body", {})

        # An attachment: has a filename AND references attachment bytes.
        if filename and body.get("attachmentId"):
            attachments.append({
                "message_id": message["id"],
                "filename": filename,
                "mime_type": part.get("mimeType"),
                "size": body.get("size"),
                "attachment_id": body["attachmentId"],
            })

    return attachments


def download_attachment(service, message_id, attachment_id):
    """Fetch and decode the raw bytes of one attachment."""
    att = service.users().messages().attachments().get(
        userId="me",
        messageId=message_id,
        id=attachment_id,
    ).execute()

    # Gmail returns URL-safe base64 with padding stripped in some cases.
    data = att["data"]
    return base64.urlsafe_b64decode(data)


def save_attachments_from_query(service, query="has:attachment",
                                out_dir="attachments", max_results=50):
    """End-to-end: search -> walk -> download -> write to disk."""
    os.makedirs(out_dir, exist_ok=True)
    saved = []

    for msg_id in list_message_ids(service, query, max_results):
        message = get_message(service, msg_id)

        subject = _header(message["payload"]["headers"], "Subject") or "(no subject)"
        sender = _header(message["payload"]["headers"], "From")
        date = _header(message["payload"]["headers"], "Date")

        for att in extract_attachment_metadata(message):
            try:
                raw = download_attachment(service, msg_id, att["attachment_id"])
            except HttpError as e:
                print(f"  failed {att['filename']}: {e}")
                continue

            # Prefix with message id to avoid filename collisions across mails.
            safe_name = f"{msg_id}_{att['filename']}"
            path = os.path.join(out_dir, safe_name)
            with open(path, "wb") as f:
                f.write(raw)

            saved.append({
                "path": path,
                "filename": att["filename"],
                "mime_type": att["mime_type"],
                "size": att["size"],
                "subject": subject,
                "from": sender,
                "date": date,
            })
            print(f"saved {safe_name} ({att['size']} bytes) — {subject}")

    return saved
