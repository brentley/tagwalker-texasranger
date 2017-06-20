// Job == tagwalker-texasranger_pipeline
node() {
    stage 'Checkout'
        checkout scm
    stage 'Build'
        sh "./build/build.sh"
    stage 'Push'
        sh "./push/push.sh"
}
