FROM python:3.12

# Create working directory
WORKDIR /app/src

ADD docker/requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple &&  rm -rf requirements.txt

# timezone & PYTHONPATH
ENV TZ="America/Los_Angeles"
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# add . director to /app
ADD . /app/

# cmd
#CMD ["/app/docker/entrypoint.sh"]
