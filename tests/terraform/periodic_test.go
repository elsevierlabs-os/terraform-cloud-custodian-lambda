package test

import (
	"archive/zip"
	"encoding/json"
	"io"
	"regexp"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// readZipEntry reads a single named file's contents out of a zip archive on disk.
func readZipEntry(t *testing.T, zipPath, entryName string) string {
	r, err := zip.OpenReader(zipPath)
	require.NoError(t, err)
	defer r.Close()

	for _, f := range r.File {
		if f.Name == entryName {
			rc, err := f.Open()
			require.NoError(t, err)
			defer rc.Close()

			data, err := io.ReadAll(rc)
			require.NoError(t, err)
			return string(data)
		}
	}

	t.Fatalf("entry %q not found in zip %q", entryName, zipPath)
	return ""
}

func TestPeriodicExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/periodic",
		Vars: map[string]interface{}{
			"create_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-periodic", lambdaFunctionName, "lambda_function_name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "periodic", modeType, "mode_type is not correct")

	periodicEventRuleName := terraform.Output(t, terraformOptions, "periodic_event_rule_name")
	assert.Equal(t, "custodian-dev-periodic", periodicEventRuleName, "periodic_event_rule_name is not correct")

	periodicScheduleExpression := terraform.Output(t, terraformOptions, "periodic_schedule_expression")
	assert.Equal(t, "rate(5 minutes)", periodicScheduleExpression, "periodic_schedule_expression is not correct")

	lambdaRole := terraform.Output(t, terraformOptions, "lambda_function_role")
	assert.Contains(t, lambdaRole, "arn:aws:iam::", "lambda_function_role should be resolved to a full ARN")
	assert.Contains(t, lambdaRole, "role/custodian-dev-periodic", "lambda_function_role should contain the expected role name")

	lambdaFunction := terraform.OutputMap(t, terraformOptions, "lambda_function")
	assert.Equal(t, "300", lambdaFunction["timeout"], "lambda_function timeout not the same as specified in policies")
	assert.Equal(t, "256", lambdaFunction["memory_size"], "lambda_function memory not the same as specified in policies")

	lambdaTags := terraform.OutputMap(t, terraformOptions, "lambda_function_tags")
	assert.Equal(t, "true", lambdaTags["Test"], "The 'Test' tag is missing or incorrect.")
	assert.Contains(t, lambdaTags["custodian-info"], "mode=periodic", "The 'custodian-info' tag should include the mode.")
	assert.Contains(t, lambdaTags["custodian-info"], "version", "The 'custodian-info' tag should include the version.")

	// Ensure expansion of {account_id} for image OwnerId filter worked
	packageLambdaResult := terraform.OutputMap(t, terraformOptions, "package_lambda_result")

	var zips map[string]struct {
		Path string `json:"path"`
	}
	require.NoError(t, json.Unmarshal([]byte(packageLambdaResult["zips"]), &zips))

	zipInfo, ok := zips["eu-west-1"]
	require.True(t, ok, "expected a packaged zip entry for eu-west-1")

	configJSON := readZipEntry(t, zipInfo.Path, "config.json")

	ownerIDPattern := regexp.MustCompile(`(?s)\{\s*"type":\s*"image",\s*"key":\s*"OwnerId".*?\}`)
	rawFilter := ownerIDPattern.FindString(configJSON)
	require.NotEmpty(t, rawFilter, "expected to find the OwnerId filter in the packaged policy")

	var valueFilter struct {
		Type  string `json:"type"`
		Key   string `json:"key"`
		Op    string `json:"op"`
		Value string `json:"value"`
	}
	require.NoError(t, json.Unmarshal([]byte(rawFilter), &valueFilter))

	filterJSON, _ := json.MarshalIndent(valueFilter, "", "  ")
	t.Logf("resolved OwnerId filter in config.json:\n%s", filterJSON)

	assert.Regexp(t, `^\d+$`, valueFilter.Value, "the resolved account_id should be numeric")

	// Get SHA256 hash from first apply
	firstSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	firstPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Second apply to ensure idempotency with the SHA256 hash
	terraform.Apply(t, terraformOptions)

	// Get SHA256 hash from second apply
	secondSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	secondPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Verify hashes are identical from first and second apply which proves idempotency
	assert.Equal(t, firstSha256Base64, secondSha256Base64,
		"Lambda source code hash (base64) should be identical across multiple applies when no changes are made")
	assert.Equal(t, firstPackageVersions, secondPackageVersions,
		"Package versions should be identical across multiple applies when no changes are made")
}
