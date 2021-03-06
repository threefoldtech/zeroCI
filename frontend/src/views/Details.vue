<template>
  <!-- begin:: Content -->
  <div class="kt-portlet kt-portlet--mobile">
    <Loading v-if="loading" />
    <div class="kt-portlet__head kt-portlet__head--lg">
      <div class="kt-portlet__head-label">
        <span class="kt-portlet__head-icon">
          <i class="kt-font-brand flaticon2-line-chart"></i>
        </span>
        <h3 class="kt-portlet__head-title">{{ repoName }}/{{ branch }}</h3>
      </div>

      <div class="kt-header__topbar pr-0">
        <button
          type="button"
          @click="viewLogs()"
          class="btn btn-primary btn-sm mr-1 text-white"
        >{{ result }}</button>

        <button
          type="button"
          class="btn btn-primary btn-sm text-white"
          :disabled="disabled"
          @click="rebuild()"
        >
          <i class="flaticon2-reload"></i> Restart build
        </button>
      </div>
    </div>
    <div class="kt-portlet__body">
      <!-- live logs -->
      <v-expansion-panels v-model="panel" v-if="live && livelogs.length > 0">
        <Live-Logs :livelogs="livelogs" />
      </v-expansion-panels>

      <v-expansion-panels v-if="live && livelogs.length > 0">
        <Neph-Logs v-for="nephID in nephIDs" :key="nephID.id" :nephID="nephID" :id="id" />
      </v-expansion-panels>

      <span v-if="live && livelogs.length < 0">No data available</span>
      <!-- logs -->
      <v-expansion-panels v-model="panel" v-if="!live">
        <logs v-for="log in logs" :key="log.id" :log="log" />
      </v-expansion-panels>

      <!-- testcases -->
      <v-expansion-panels v-if="!live">
        <test-suites
          v-for="testsuite in testsuites"
          :key="testsuite.id"
          :testsuite="testsuite"
          :index="testsuite.id"
        />
      </v-expansion-panels>
    </div>
  </div>
  <!-- end:: Content -->
</template>

<script>
import EventService from "../services/EventService";
import LiveLogs from "../components/LiveLogs";
import NephLogs from "../components/NephLogs";
import Logs from "../components/Logs";
import TestSuites from "../components/TestSuites";
import Loading from "../components/Loading";
export default {
  name: "RepoDetails",
  props: ["orgName", "repoName", "branch", "id"],
  components: {
    "Live-Logs": LiveLogs,
    "Neph-Logs": NephLogs,
    logs: Logs,
    Loading: Loading,
    "test-suites": TestSuites
  },
  data() {
    return {
      loading: true,
      panel: 0,
      live: false,
      result: "View Logs",
      logs: [],
      livelogs: [],
      testsuites: [],
      disabled: false,
      nephIDs: []
    };
  },
  methods: {
    connect() {
      if (process.env.NODE_ENV === "development") {
        this.socket = new WebSocket(
          "ws://" + window.location.hostname + `/websocket/logs/${this.id}`
        );
      } else {
        this.socket = new WebSocket(
          "wss://" + window.location.hostname + `/websocket/logs/${this.id}`
        );
      }
      this.socket.onopen = () => {
        console.log("connecting...");
        this.socket.onmessage = ({ data }) => {
          this.livelogs = data;
        };
      };
    },
    nephConnect() {
      if (process.env.NODE_ENV === "development") {
        this.nephID = new WebSocket(
          "ws://" + window.location.hostname + `/websocket/neph_jobs/${this.id}`
        );
      } else {
        this.nephID = new WebSocket(
          "wss://" +
            window.location.hostname +
            `/websocket/neph_jobs/${this.id}`
        );
      }
      this.nephID.onopen = () => {
        this.nephID.onmessage = ({ data }) => {
          this.nephIDs = JSON.parse(data);
        };
      };
    },
    fetchBrancheIdDetails() {
      this.loading = true;
      EventService.getBranchIdDetails(
        this.orgName + "/" + this.repoName,
        this.branch,
        this.id
      )
        .then(response => {
          this.loading = false;
          if (response.data.live) {
            this.viewLogs();
          } else {
            response.data.result.map((job, index) => {
              if (job.type == "log") {
                this.logs.push(job);
              } else if (job.type == "testsuite") {
                this.testsuites.push(job);
              }
            });
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    rebuild() {
      if (this.$store.state.user !== null) {
        this.loading = true;
        EventService.restartBuildId(this.id)
          .then(response => {
            if (response) {
              this.loading = false;
              this.disabled = true;
            }
          })
          .catch(error => {
            console.log("Error! Could not reach the API. " + error);
          });
      } else {
        toastr.error("Please Login First!");
      }
    },
    viewLogs() {
      this.live = !this.live;
      if (this.live) {
        this.result = "View Result";
        this.connect();
      } else {
        this.result = "View Logs";
      }
    }
  },
  created() {
    this.fetchBrancheIdDetails();
    this.nephConnect();
  }
};
</script>

<style scoped>
.v-expansion-panels {
  margin-bottom: 10px;
}

.kt-portlet__head-icon {
  text-align: left;
}
</style>
