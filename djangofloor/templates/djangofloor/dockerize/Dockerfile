# Start with a Python image.
FROM python:3.6-slim

# Some stuff that everyone has been copy-pasting
# since the dawn of time.
ENV PYTHONUNBUFFERED 1

# Install some necessary things.
RUN apt-get update
RUN mkdir -p "{{ tmp_dir.1 }}"
WORKDIR "{{ tmp_dir.1 }}"
COPY "./{{ dist_filename }}" "{{ tmp_dir.1 }}/{{ dist_filename }}"
COPY "./install_python.sh" "{{ tmp_dir.1 }}/install_python.sh"
COPY "./install_project.sh" "{{ tmp_dir.1 }}/install_project.sh"
COPY "./install_dependencies.sh" "{{ tmp_dir.1 }}/install_dependencies.sh"
COPY "./configure_project.sh" "{{ tmp_dir.1 }}/configure_project.sh"
COPY "./run_project.sh" "{{ tmp_dir.1 }}/run_project.sh"

RUN ["bash", "{{ tmp_dir.1 }}/install_python.sh"]
RUN ["bash", "{{ tmp_dir.1 }}/install_project.sh"]
RUN ["bash", "{{ tmp_dir.1 }}/install_dependencies.sh"]
#CMD ["{{ tmp_dir.1 }}/configure_project.sh"]
#CMD ["{{ tmp_dir.1 }}/run_project.sh"]
