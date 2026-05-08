#!/bin/bash
# EVENT_HORIZON Final Build Script

set -e

echo "🏗️  Building EVENT_HORIZON Final Release..."

# Create build directory
BUILD_DIR="build"
mkdir -p $BUILD_DIR

# Copy source files
echo "📦 Copying source files..."
cp -r core $BUILD_DIR/
cp -r layers $BUILD_DIR/
cp -r config $BUILD_DIR/
cp -r tests $BUILD_DIR/
cp __init__.py $BUILD_DIR/
cp main.py $BUILD_DIR/
cp requirements.txt $BUILD_DIR/
cp setup.py $BUILD_DIR/
cp README.md $BUILD_DIR/

# Copy architectural corrections
echo "🔧 Copying architectural corrections..."
cp core/trust_boundaries.py $BUILD_DIR/core/
cp core/causal_topology.py $BUILD_DIR/core/
cp core/advanced_concurrency.py $BUILD_DIR/core/
cp core/oracle_validation.py $BUILD_DIR/core/
cp core/architectural_corrections.py $BUILD_DIR/core/
cp core/enterprise_architecture.py $BUILD_DIR/core/
cp core/final_architecture.py $BUILD_DIR/core/
cp core/epistemic_layer.py $BUILD_DIR/core/

# Create deployment package
echo "📦 Creating deployment package..."
cd $BUILD_DIR
tar -czf event_horizon_final.tar.gz .
cd ..

# Generate checksum
echo "🔐 Generating checksum..."
shasum -a 256 $BUILD_DIR/event_horizon_final.tar.gz > $BUILD_DIR/checksum.txt

echo "✅ Build complete!"
echo "📦 Package: $BUILD_DIR/event_horizon_final.tar.gz"
echo "🔐 Checksum: $BUILD_DIR/checksum.txt"
echo ""
echo "🚀 Ready for deployment to dsmoto.ru"
