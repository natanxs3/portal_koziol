pipeline {
  agent { label 'agent_koziol' }
  options {
    disableConcurrentBuilds()
    timestamps()
    skipDefaultCheckout(true)
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }
  triggers { pollSCM('H/3 * * * *') }
  parameters {
    choice(name: 'SRODOWISKO', choices: ['TEST', 'PROD'], description: 'TEST tworzy paczke; PROD promuje przetestowana paczke.')
    string(name: 'WERSJA', defaultValue: '', description: 'Numer udanego budowania TEST do wdrozenia na PROD.')
  }
  stages {
    stage('Kod z main') {
      steps {
        deleteDir()
        checkout scm
        sh 'test "$(git branch --show-current)" = main || test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"'
      }
    }
    stage('Kontrola Ansible') {
      when { expression { params.SRODOWISKO == 'TEST' } }
      steps {
        sh 'ansible-lint wdrozenie_portalu.yml'
        sh 'ansible-playbook wdrozenie_portalu.yml --syntax-check'
      }
    }
    stage('Paczka z wersja') {
      when { expression { params.SRODOWISKO == 'TEST' } }
      steps {
        sh '''python3 - <<'PY'
import datetime, json, os, subprocess
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
with open('strona/version.json', 'w') as f:
    json.dump({'build': os.environ['BUILD_NUMBER'], 'commit': commit,
               'data': datetime.datetime.now(datetime.timezone.utc).isoformat()}, f)
PY
tar -czf portal.tar.gz strona wdrozenie_portalu.yml zadania inventory.yml ansible.cfg requirements.yml ci
mkdir paczka
tar -xzf portal.tar.gz -C paczka'''
      }
    }
    stage('Pobranie przetestowanej wersji') {
      when { expression { params.SRODOWISKO == 'PROD' } }
      steps {
        script {
          if (!(params.WERSJA ==~ /[1-9][0-9]*/)) { error('Podaj numer budowania TEST w WERSJA.') }
        }
        copyArtifacts(projectName: 'portal_koziol', selector: specific(params.WERSJA), filter: 'portal.tar.gz', fingerprintArtifacts: true)
        sh 'mkdir paczka && tar -xzf portal.tar.gz -C paczka'
        script {
          def manifest = readJSON(file: 'paczka/strona/version.json')
          if (manifest.build.toString() != params.WERSJA) { error('Numer paczki rozni sie od wybranego budowania.') }
          input(message: "Wdrozyc na PROD paczke TEST #${manifest.build}, commit ${manifest.commit}?", ok: 'Wdrozenie PROD')
        }
      }
    }
    stage('Wdrozenie Ansible') {
      steps {
        dir('paczka') {
          ansiblePlaybook(playbook: 'wdrozenie_portalu.yml', inventory: 'inventory.yml', credentialsId: 'deploy_koziol', limit: params.SRODOWISKO == 'TEST' ? 'test' : 'prod')
        }
      }
    }
    stage('Test HTTP, health i wersji') {
      steps {
        withEnv(["CEL=${params.SRODOWISKO}", "OCZEKIWANY_BUILD=${params.SRODOWISKO == 'TEST' ? env.BUILD_NUMBER : params.WERSJA}"]) {
          sh 'python3 paczka/ci/test_portal.py'
        }
      }
    }
    stage('Archiwum po udanym tescie TEST') {
      when { expression { params.SRODOWISKO == 'TEST' } }
      steps { archiveArtifacts(artifacts: 'portal.tar.gz', fingerprint: true, onlyIfSuccessful: true) }
    }
  }
  post {
    failure {
      emailext(to: 'nk316070@student.polsl.pl', subject: "BLAD: ${env.JOB_NAME} #${env.BUILD_NUMBER}", body: "Srodowisko: ${params.SRODOWISKO}\nLog: ${env.BUILD_URL}console")
    }
  }
}
