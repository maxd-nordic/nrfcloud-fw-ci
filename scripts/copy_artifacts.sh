#!/usr/env bash

# take three args, sample_name, build_dir, artifacts_dir

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 sample_name build_dir artifacts_dir"
    exit 1
fi

SAMPLE_NAME=$1
BUILD_DIR=$2
ARTIFACTS_DIR=$3
BUILD_BASENAME=$(basename $BUILD_DIR)
TARGET_DIR=$ARTIFACTS_DIR/$BUILD_BASENAME

mkdir -p $TARGET_DIR
cp $BUILD_DIR/dfu_application.zip $TARGET_DIR
cp $BUILD_DIR/dfu_mcuboot.zip $TARGET_DIR
cp $BUILD_DIR/partitions.yml $TARGET_DIR
cp $BUILD_DIR/build_info.yml $TARGET_DIR
cp $BUILD_DIR/merged*.hex $TARGET_DIR
cp $BUILD_DIR/zephyr/.config $TARGET_DIR/zephyr-dotconfig.txt
cp $BUILD_DIR/$SAMPLE_NAME/zephyr/.config $TARGET_DIR/app-dotconfig.txt
cp $BUILD_DIR/$SAMPLE_NAME/zephyr/.config.sysbuild $TARGET_DIR/app-dotconfig.sysbuild.txt
cp $BUILD_DIR/$SAMPLE_NAME/zephyr/zephyr.signed.hex $TARGET_DIR
cp $BUILD_DIR/$SAMPLE_NAME/zephyr/zephyr.dts $TARGET_DIR
cp $BUILD_DIR/$SAMPLE_NAME/zephyr/log_dictionary.json $TARGET_DIR

exit 0
