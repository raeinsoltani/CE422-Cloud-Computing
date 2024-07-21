# Build dependencies
FROM python:3.9.19-alpine as builder

RUN apk update && \
    apk add --no-cache gcc musl-dev python3-dev

COPY ./requirements.txt /requirements.txt

RUN pip3 install --no-cache-dir -r /requirements.txt

# Final image
FROM python:3.9.19-alpine

COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY ./cc_hw2_hello.py /hello_script.py

CMD ["python", "./hello_script.py"]
