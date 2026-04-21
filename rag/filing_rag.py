from sentence_transformers import SentenceTransformer
from db.database import SessionLocal
from db.models import FilingChunk
from edgar import Company, set_identity
from datetime import date
from sqlalchemy import func 


model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')



def chunk_text(text, chunk_size: int = 500, overlap = 50):
    l, r = 0, chunk_size 
    chunk_text = []
    while r < len(text):
        chunk_text.append(text[l : r])
        l += (chunk_size - overlap)
        r += chunk_size
    chunk_text.append(text[l : ])

    return chunk_text


def embed_chunks(chunks):
    embeddings = model.encode(chunks)
    return embeddings


def store_chunks(ticker, section, chunks, embeddings, filing_date):
    db = SessionLocal()
    try:

        chunk_filing_rows = [FilingChunk(ticker=ticker, section=section, chunk_text = chunks[i], embedding = embeddings[i], filing_date = filing_date) 
                            for i in range(len(chunks))]
        db.add_all(chunk_filing_rows)
        db.commit()
    finally:
        db.close()
    return "Row added"



def fetch_sec_filings(ticker: str):
    set_identity("Shakur Ahmad shakur-ahmad@outlook.com")
    c = Company(ticker)
    ten_k_filing = c.get_filings(form='10-K').latest()
    if ten_k_filing is None:
        raise Exception
    ten_k_date = ten_k_filing.filing_date
    ten_k = ten_k_filing.obj()
    try:
        eight_k_filing = c.get_filings(form='8-K').latest()
        if eight_k_filing is None:
            raise Exception
        else:
            eight_k_date = eight_k_filing.filing_date
            eight_k = eight_k_filing.obj()

    except:
        eight_k = None
        eight_k_date = None
        print(f'8K form missing for {c}')

    sec_filings = [                                                                                                                                                         
      {'section': 'management_discussion', 'text': ten_k.management_discussion, 'date': ten_k_date},                                                                              
      {'section': 'risk_factors', 'text': ten_k.risk_factors, 'date': ten_k_date},                                                                                       
      {'section': 'eight_k', 'text': eight_k.text() if eight_k else None, 'date': eight_k_date},
    ]        
    return sec_filings


def process_filing(ticker):
    db = SessionLocal()
    try:
        sec_filings = fetch_sec_filings(ticker)
        for sec_filing in sec_filings:
            if not sec_filing['text']:
                continue
            if db.query(FilingChunk).filter(FilingChunk.ticker == ticker).\
                filter(func.date(FilingChunk.filing_date) == sec_filing['date']).first() == None:
                chunks = chunk_text(sec_filing['text'])
                embeddings = embed_chunks(chunks)
                store = store_chunks(ticker, sec_filing['section'], chunks, embeddings, sec_filing['date'])
    except Exception as e:
        print(e)
    finally:
        db.close()


def retrieve_chunks(query, ticker, top_k = 5):
    embeded = model.encode(query)
    db = SessionLocal()
    try:
        top_k_chunks = db.query(FilingChunk).filter(FilingChunk.ticker == ticker).order_by(FilingChunk.embedding.op('<=>')(embeded)).limit(top_k).all()
    finally:
        db.close()
    return top_k_chunks 


if __name__ == "__main__":                                                                                                                                
    chunks = retrieve_chunks("What are the main supply chain risks?", "AAPL")                                                                             
    for c in chunks:                                                                                                                                      
        print(c.section, c.chunk_text[:200])                                                                                                              
        print("---")  


            
