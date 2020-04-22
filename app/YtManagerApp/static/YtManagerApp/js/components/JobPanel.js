export class JobEntry
{
    id = "";
    description = "";
    message = "";
    progress = 0;

    dom = null;

    constructor(job)
    {
        this.id = job.id;
        this.description = job.description;
        this.message = job.message;
        this.progress = job.progress;
    }

    createDom(template, parent)
    {
        this.dom = template.clone();
        this.dom.attr('id', `job_${this.id}`);
        this.dom.addClass('job_entry');
        this.dom.removeClass('collapse');

        this.updateDom();

        this.dom.appendTo(parent);
    }

    update(job)
    {
        if (job !== null) {
            this.description = job.description;
            this.message = job.message;
            this.progress = job.progress;
        }

        this.updateDom();
    }

    updateDom()
    {
        if (this.dom === null) {
            return;
        }
        this.dom.find('#job_panel_item_title').text(this.description);
        this.dom.find('#job_panel_item_subtitle').text(this.message);

        let entryPercent = 100 * this.progress;
        let jobEntryProgress = this.dom.find('#job_panel_item_progress');
        jobEntryProgress.width(entryPercent + '%');
        jobEntryProgress.text(`${entryPercent.toFixed(0)}%`);
    }

    deleteDom()
    {
        if (this.dom === null) {
            return;
        }
        this.dom.remove();
        this.dom = null;
    }
}

export class JobPanel
{
    static QUERY_INTERVAL = 1500;

    statusBar_Progress = null;
    panel = null;
    panel_Title = null;
    panel_TitleNoJobs = null;
    panel_JobTemplate = null;

    jobs = [];

    constructor()
    {
        this.statusBar_Progress = $('#status-progress');
        this.panel = $('#job_panel');
        this.panel_Title = this.panel.find('#job_panel_title');
        this.panel_TitleNoJobs = this.panel.find('#job_panel_no_jobs_title');
        this.panel_JobTemplate = this.panel.find('#job_panel_item_template');
    }

    update()
    {
        let pThis = this;

        $.get(window.ytsmContext.url_ajax_get_running_jobs)
            .done(function(data, textStatus, jqXHR) {
                if (jqXHR.getResponseHeader('content-type') === "application/json") {
                    pThis._updateInternal(data);
                }
                else {
                    pThis._clear();
                }
            });
    }

    _updateInternal(data)
    {
        this._updateJobs(data);
        this._updateStatusBar();
        this._updateProgressBar();
        this._updateTitle();

        $('#btn_toggle_job_panel').dropdown('update');
    }

    _updateJobs(data)
    {
        let keep = [];

        for (let srvJob of data)
        {
            let found = false;

            // Find existing jobs
            for (let job of this.jobs) {
                if (job.id === srvJob.id) {
                    job.update(srvJob);
                    found = true;
                    keep.push(job.id);
                }
            }

            // New job
            if (!found) {
                let job = new JobEntry(srvJob);
                job.createDom(this.panel_JobTemplate, this.panel);
                this.jobs.push(job);
                keep.push(job.id);
            }
        }

        // Delete old jobs
        for (let i = 0; i < this.jobs.length; i++) {
            if (keep.indexOf(this.jobs[i].id) < 0) {
                this.jobs[i].deleteDom();
                this.jobs.splice(i--, 1);
            }
        }
    }

    _clear()
    {
        // Delete old jobs
        for (let i = 0; i < this.jobs.length; i++) {
            this.jobs[i].deleteDom();
        }
        this.jobs = [];
    }

    _updateTitle()
    {
        if (this.jobs.length === 0) {
            this.panel_Title.addClass('collapse');
            this.panel_TitleNoJobs.removeClass('collapse');
        }
        else {
            this.panel_Title.removeClass('collapse');
            this.panel_TitleNoJobs.addClass('collapse');
        }
    }

    _updateStatusBar()
    {
        let text = "";

        if (this.jobs.length === 1) {
            text = `${this.jobs[0].description} | ${this.jobs[0].message}`;
        }
        else if (this.jobs.length > 1) {
            text = `Running ${this.jobs.length} jobs...`;
        }
        $('#status-message').text(text);
    }

    _updateProgressBar()
    {
        if (this.jobs.length > 0) {
            // Make visible
            this.statusBar_Progress.removeClass('invisible');

            // Calculate progress
            let combinedProgress = 0;
            for (let job of this.jobs) {
                combinedProgress += job.progress;
            }

            let percent = 100 * combinedProgress / this.jobs.length;

            let bar = this.statusBar_Progress.find('.progress-bar');
            bar.width(percent + '%');
            bar.text(`${percent.toFixed(0)}%`);
        }
        else {
            // hide
            this.statusBar_Progress.addClass('invisible');
        }
    }

    enable()
    {
        this.update();

        let pThis = this;
        setInterval(function() {
            pThis.update();
        }, JobPanel.QUERY_INTERVAL);
    }
}